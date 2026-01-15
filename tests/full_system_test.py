#!/usr/bin/env python3
"""
ZenAi Full System Test / ZenAi 全流程测试

Full-cycle autonomous test:
- Random concurrent user inputs via API
- Passive observation of automatic iterations
- Comprehensive reporting

完全自主流程测试：
- 通过 API 随机并发用户输入
- 被动观察自动迭代
- 详细测试报告

Usage:
    python tests/full_system_test.py data/test_inputs.jsonl
    python tests/full_system_test.py data/test_inputs.jsonl --output reports/full_test_report.json
"""
import argparse
import asyncio
import json
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp


API_URL = "http://localhost:8000"


@dataclass
class TestConfig:
    """Test configuration"""
    input_file: Path
    output_file: Path | None
    api_url: str
    min_batch_size: int = 8
    max_batch_size: int = 25
    min_concurrent: int = 3
    max_concurrent: int = 10
    batch_delay_min: float = 2.0
    batch_delay_max: float = 5.0
    target_iterations: int = 2
    max_wait_iterations: int = 300
    check_interval: float = 5.0
    verbose: bool = False


@dataclass
class TestStats:
    """Test statistics"""
    start_time: datetime
    end_time: datetime | None = None
    total_inputs: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_feedbacks: int = 0
    observed_iterations: int = 0
    initial_iterations: int = 0
    batches: list[dict[str, Any]] = field(default_factory=list)
    status_snapshots: list[dict[str, Any]] = field(default_factory=list)
    iteration_records: list[dict[str, Any]] = field(default_factory=list)


class FullSystemTest:
    """Full system test orchestrator - Injector and Observer only"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.stats = TestStats(start_time=datetime.utcnow())
        self.test_cases: list[dict[str, Any]] = []
        self.results: list[dict[str, Any]] = []
        
    async def check_api_health(self) -> bool:
        """Check if API server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.api_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def get_system_status(self) -> dict[str, Any]:
        """Get current system status via API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.api_url}/status",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except Exception as e:
            if self.config.verbose:
                print(f"Warning: Failed to get system status: {e}")
            return {}
    
    async def get_system_metrics(self) -> dict[str, Any]:
        """Get current system metrics via API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.api_url}/metrics",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except Exception as e:
            if self.config.verbose:
                print(f"Warning: Failed to get system metrics: {e}")
            return {}
    
    async def send_chat_request(
        self,
        user_input: str,
        session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        """Send a single chat request via API"""
        try:
            async with session.post(
                f"{self.config.api_url}/chat",
                json={"user_input": user_input},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "user_input": user_input,
                        "interaction_id": result["interaction_id"],
                        "response_text": result["response_text"],
                        "refusal": result.get("refusal", False),
                        "prompt_version": result.get("prompt_version", 0),
                        "timestamp": result.get("timestamp", ""),
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "user_input": user_input,
                        "error": f"HTTP {response.status}: {error_text}",
                    }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "user_input": user_input,
                "error": "Request timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "user_input": user_input,
                "error": str(e),
            }
    
    async def send_feedback(
        self,
        interaction_id: int,
        feedback: str,
        session: aiohttp.ClientSession
    ) -> bool:
        """Send feedback for an interaction via API"""
        try:
            async with session.post(
                f"{self.config.api_url}/feedback",
                json={"interaction_id": interaction_id, "feedback": feedback},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
        except Exception as e:
            if self.config.verbose:
                print(f"  Warning: Failed to send feedback: {e}")
            return False
    
    async def run_batch(
        self,
        batch_num: int,
        cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Run a batch of concurrent requests"""
        batch_size = len(cases)
        concurrent = random.randint(
            self.config.min_concurrent,
            min(self.config.max_concurrent, batch_size)
        )
        
        print(f"\n[Batch {batch_num}] Injecting {batch_size} requests "
              f"with concurrency={concurrent}")
        
        batch_start = time.time()
        batch_results = []
        
        async with aiohttp.ClientSession() as session:
            # Run requests in concurrent groups
            for i in range(0, batch_size, concurrent):
                group = cases[i:i+concurrent]
                tasks = [
                    self.send_chat_request(case["user_input"], session)
                    for case in group
                ]
                group_results = await asyncio.gather(*tasks)
                batch_results.extend(group_results)
                
                # Small delay between concurrent groups
                if i + concurrent < batch_size:
                    await asyncio.sleep(0.2)
            
            # Send feedback for successful requests
            feedback_tasks = []
            for result, case in zip(batch_results, cases):
                if result["success"] and "feedback" in case:
                    feedback_tasks.append(
                        self.send_feedback(
                            result["interaction_id"],
                            case["feedback"],
                            session
                        )
                    )
            
            if feedback_tasks:
                feedback_results = await asyncio.gather(*feedback_tasks)
                feedback_count = sum(1 for r in feedback_results if r)
                self.stats.total_feedbacks += feedback_count
                if self.config.verbose:
                    print(f"  Sent {feedback_count} feedbacks")
        
        batch_duration = time.time() - batch_start
        
        # Update stats
        successful = sum(1 for r in batch_results if r["success"])
        failed = batch_size - successful
        self.stats.total_requests += batch_size
        self.stats.successful_requests += successful
        self.stats.failed_requests += failed
        
        batch_info = {
            "batch_num": batch_num,
            "size": batch_size,
            "concurrent": concurrent,
            "successful": successful,
            "failed": failed,
            "duration": batch_duration,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.stats.batches.append(batch_info)
        self.results.extend(batch_results)
        
        print(f"  Success: {successful}/{batch_size}, "
              f"Duration: {batch_duration:.2f}s")
        
        return batch_info
    
    async def observe_status(self) -> None:
        """Observe and record system status"""
        status = await self.get_system_status()
        metrics = await self.get_system_metrics()
        
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "metrics": metrics,
        }
        self.stats.status_snapshots.append(snapshot)
        
        # Check for new iterations
        current_iterations = status.get("total_iterations", 0)
        if current_iterations > self.stats.observed_iterations:
            new_iterations = current_iterations - self.stats.observed_iterations
            self.stats.observed_iterations = current_iterations
            
            print(f"\n{'='*70}")
            print(f"[Observer] Detected {new_iterations} new iteration(s)!")
            print(f"[Observer] Total iterations now: {current_iterations}")
            print(f"  Prompt Version: {status.get('prompt_version', 'N/A')}")
            print(f"  Total Interactions: {status.get('total_interactions', 0)}")
            if metrics.get("metrics"):
                print(f"  Latest Metrics:")
                for key, value in metrics["metrics"].items():
                    print(f"    {key}: {value}")
            print(f"{'='*70}\n")
            
            # Record iteration
            self.stats.iteration_records.append({
                "iteration_id": metrics.get("iteration_id"),
                "detected_at": datetime.utcnow().isoformat(),
                "total_interactions": metrics.get("total_interactions", 0),
                "metrics": metrics.get("metrics"),
                "status": status,
            })
    
    def load_test_cases(self) -> None:
        """Load test cases from input file"""
        print(f"\nLoading test cases from: {self.config.input_file}")
        
        with open(self.config.input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    case = json.loads(line)
                    if "user_input" not in case:
                        print(f"Warning: Line {line_num} missing 'user_input'")
                        continue
                    self.test_cases.append(case)
                except json.JSONDecodeError as e:
                    print(f"Warning: Line {line_num} invalid JSON: {e}")
                    continue
        
        self.stats.total_inputs = len(self.test_cases)
        print(f"Loaded {self.stats.total_inputs} test cases")
    
    async def run_test(self) -> None:
        """Run full system test as injector and observer"""
        print("\n" + "=" * 70)
        print("ZenAi Full System Test / ZenAi 全流程测试")
        print("Mode: Autonomous - Injector and Observer / 模式：自主 - 注入与观察")
        print("=" * 70)
        
        # Check API health
        print("\nChecking API server...")
        if not await self.check_api_health():
            print(f"Error: API server is not running at {self.config.api_url}")
            print("Please start the API server first:")
            print("  bash start.sh")
            sys.exit(1)
        print("✓ API server is ready")
        
        # Get initial status
        initial_status = await self.get_system_status()
        self.stats.initial_iterations = initial_status.get("total_iterations", 0)
        self.stats.observed_iterations = self.stats.initial_iterations
        
        print(f"\nInitial System Status:")
        print(f"  Prompt Version: {initial_status.get('prompt_version', 'N/A')}")
        print(f"  Total Interactions: {initial_status.get('total_interactions', 0)}")
        print(f"  Total Iterations: {self.stats.initial_iterations}")
        print(f"  System Frozen: {initial_status.get('frozen', False)}")
        print(f"  System Killed: {initial_status.get('killed', False)}")
        
        # Load test cases
        self.load_test_cases()
        
        if not self.test_cases:
            print("Error: No valid test cases found")
            sys.exit(1)
        
        # Shuffle test cases for random distribution
        random.shuffle(self.test_cases)
        
        print(f"\nTest Configuration:")
        print(f"  Batch size: {self.config.min_batch_size}-{self.config.max_batch_size}")
        print(f"  Concurrent requests: {self.config.min_concurrent}-{self.config.max_concurrent}")
        print(f"  Target new iterations: {self.config.target_iterations}")
        print(f"  Batch delay: {self.config.batch_delay_min}-{self.config.batch_delay_max}s")
        print(f"  Status check interval: {self.config.check_interval}s")
        
        # Run batches
        print("\n" + "=" * 70)
        print("Starting Data Injection / 开始数据注入")
        print("=" * 70)
        
        remaining = self.test_cases.copy()
        batch_num = 0
        
        while remaining:
            batch_num += 1
            
            # Determine batch size
            batch_size = random.randint(
                self.config.min_batch_size,
                min(self.config.max_batch_size, len(remaining))
            )
            
            batch_cases = remaining[:batch_size]
            remaining = remaining[batch_size:]
            
            # Run batch
            await self.run_batch(batch_num, batch_cases)
            
            # Observe status after batch
            await self.observe_status()
            
            # Random delay between batches
            if remaining:
                delay = random.uniform(
                    self.config.batch_delay_min,
                    self.config.batch_delay_max
                )
                if self.config.verbose:
                    print(f"  Waiting {delay:.1f}s before next batch...")
                await asyncio.sleep(delay)
        
        # Observation phase - wait for target iterations
        new_iterations_needed = self.config.target_iterations - (
            self.stats.observed_iterations - self.stats.initial_iterations
        )
        
        if new_iterations_needed > 0:
            print("\n" + "=" * 70)
            print(f"Observation Phase / 观察阶段")
            print(f"Waiting for {new_iterations_needed} more iteration(s) to occur...")
            print("=" * 70)
            
            wait_count = 0
            while wait_count < self.config.max_wait_iterations:
                await asyncio.sleep(self.config.check_interval)
                await self.observe_status()
                
                new_iterations = self.stats.observed_iterations - self.stats.initial_iterations
                if new_iterations >= self.config.target_iterations:
                    print(f"\n✓ Target iterations reached: {new_iterations}")
                    break
                
                wait_count += 1
                if wait_count % 10 == 0:
                    print(f"  Still waiting... ({new_iterations}/{self.config.target_iterations} "
                          f"iterations observed, {wait_count * self.config.check_interval:.0f}s elapsed)")
            
            if wait_count >= self.config.max_wait_iterations:
                print(f"\n⚠ Max wait time reached. Only observed "
                      f"{self.stats.observed_iterations - self.stats.initial_iterations} "
                      f"iteration(s).")
        
        # Get final status
        print("\n" + "=" * 70)
        print("Getting Final System Status / 获取最终系统状态")
        print("=" * 70)
        
        final_status = await self.get_system_status()
        final_metrics = await self.get_system_metrics()
        
        print(f"\nFinal System Status:")
        print(f"  Prompt Version: {final_status.get('prompt_version', 'N/A')}")
        print(f"  Total Interactions: {final_status.get('total_interactions', 0)}")
        print(f"  Total Iterations: {final_status.get('total_iterations', 0)}")
        print(f"  System Frozen: {final_status.get('frozen', False)}")
        print(f"  System Killed: {final_status.get('killed', False)}")
        
        if final_metrics.get("metrics"):
            print(f"\nFinal Metrics:")
            for key, value in final_metrics["metrics"].items():
                print(f"  {key}: {value}")
        
        self.stats.end_time = datetime.utcnow()
    
    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive test report"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()
        
        report = {
            "test_summary": {
                "start_time": self.stats.start_time.isoformat(),
                "end_time": self.stats.end_time.isoformat() if self.stats.end_time else None,
                "duration_seconds": duration,
                "total_inputs": self.stats.total_inputs,
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "success_rate": (
                    self.stats.successful_requests / self.stats.total_requests * 100
                    if self.stats.total_requests > 0 else 0
                ),
                "total_feedbacks": self.stats.total_feedbacks,
                "initial_iterations": self.stats.initial_iterations,
                "final_iterations": self.stats.observed_iterations,
                "new_iterations": self.stats.observed_iterations - self.stats.initial_iterations,
                "total_batches": len(self.stats.batches),
            },
            "batches": self.stats.batches,
            "iterations": self.stats.iteration_records,
            "status_snapshots": self.stats.status_snapshots,
            "results": self.results,
        }
        
        return report
    
    def print_summary(self) -> None:
        """Print test summary"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("Test Summary / 测试摘要")
        print("=" * 70)
        
        print(f"\nTime / 时间:")
        print(f"  Start: {self.stats.start_time}")
        print(f"  End: {self.stats.end_time}")
        print(f"  Duration: {duration:.2f}s ({duration/60:.1f} minutes)")
        
        print(f"\nData Injection / 数据注入:")
        print(f"  Total Inputs: {self.stats.total_inputs}")
        print(f"  Total Requests: {self.stats.total_requests}")
        print(f"  Successful: {self.stats.successful_requests}")
        print(f"  Failed: {self.stats.failed_requests}")
        if self.stats.total_requests > 0:
            print(f"  Success Rate: {self.stats.successful_requests/self.stats.total_requests*100:.1f}%")
        print(f"  Feedbacks Sent: {self.stats.total_feedbacks}")
        
        print(f"\nBatches / 批次:")
        print(f"  Total Batches: {len(self.stats.batches)}")
        if self.stats.batches:
            avg_batch_size = sum(b["size"] for b in self.stats.batches) / len(self.stats.batches)
            avg_concurrent = sum(b["concurrent"] for b in self.stats.batches) / len(self.stats.batches)
            print(f"  Average Batch Size: {avg_batch_size:.1f}")
            print(f"  Average Concurrency: {avg_concurrent:.1f}")
        
        print(f"\nSystem Evolution / 系统演化:")
        print(f"  Initial Iterations: {self.stats.initial_iterations}")
        print(f"  Final Iterations: {self.stats.observed_iterations}")
        print(f"  New Iterations Observed: {self.stats.observed_iterations - self.stats.initial_iterations}")
        
        if self.stats.iteration_records:
            print(f"\n  Iteration Details:")
            for rec in self.stats.iteration_records:
                print(f"    Iteration {rec.get('iteration_id', 'N/A')}: "
                      f"Detected at {rec['detected_at']}, "
                      f"Interactions={rec['total_interactions']}")
        
        print("\n" + "=" * 70)


async def main_async(args):
    """Async main function"""
    config = TestConfig(
        input_file=Path(args.input_file),
        output_file=Path(args.output) if args.output else None,
        api_url=args.api_url,
        min_batch_size=args.min_batch_size,
        max_batch_size=args.max_batch_size,
        min_concurrent=args.min_concurrent,
        max_concurrent=args.max_concurrent,
        batch_delay_min=args.batch_delay_min,
        batch_delay_max=args.batch_delay_max,
        target_iterations=args.iterations,
        max_wait_iterations=args.max_wait,
        check_interval=args.check_interval,
        verbose=args.verbose,
    )
    
    test = FullSystemTest(config)
    
    try:
        await test.run_test()
        test.print_summary()
        
        # Save report
        report = test.generate_report()
        
        if config.output_file:
            config.output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config.output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Report saved to: {config.output_file}")
        
        # Exit with error if any requests failed
        if test.stats.failed_requests > 0:
            print(f"\n⚠ Warning: {test.stats.failed_requests} requests failed")
            return 1
        
        # Exit with error if target iterations not reached
        new_iterations = test.stats.observed_iterations - test.stats.initial_iterations
        if new_iterations < config.target_iterations:
            print(f"\n⚠ Warning: Only {new_iterations} iteration(s) observed, "
                  f"target was {config.target_iterations}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        test.stats.end_time = datetime.utcnow()
        test.print_summary()
        return 130
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="ZenAi Full System Test - Autonomous Mode / ZenAi 全流程测试 - 自主模式"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Input JSONL file with test cases / 测试用例 JSONL 文件"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/full_test_report.json",
        help="Output JSON file for report / 报告输出 JSON 文件"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL / API 基础地址"
    )
    parser.add_argument(
        "--min-batch-size",
        type=int,
        default=8,
        help="Minimum batch size / 最小批次大小"
    )
    parser.add_argument(
        "--max-batch-size",
        type=int,
        default=25,
        help="Maximum batch size / 最大批次大小"
    )
    parser.add_argument(
        "--min-concurrent",
        type=int,
        default=3,
        help="Minimum concurrent requests / 最小并发数"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=10,
        help="Maximum concurrent requests / 最大并发数"
    )
    parser.add_argument(
        "--batch-delay-min",
        type=float,
        default=2.0,
        help="Minimum delay between batches (seconds) / 批次间最小延迟（秒）"
    )
    parser.add_argument(
        "--batch-delay-max",
        type=float,
        default=5.0,
        help="Maximum delay between batches (seconds) / 批次间最大延迟（秒）"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=2,
        help="Target number of new iterations to observe / 目标观察的新迭代次数"
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=300,
        help="Maximum wait cycles for iterations / 等待迭代的最大周期数"
    )
    parser.add_argument(
        "--check-interval",
        type=float,
        default=5.0,
        help="Status check interval (seconds) / 状态检查间隔（秒）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output / 打印详细输出"
    )
    
    args = parser.parse_args()
    
    # Check input file
    if not Path(args.input_file).exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Run async main
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
