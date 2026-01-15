#!/usr/bin/env python3
"""
ZenAi Batch Test Script / ZenAi 批量测试脚本

Assumes main API server is already running.
假设主程序 API 服务器已经在运行。

Usage:
    ./batch_test.py data/test_inputs.jsonl
    ./batch_test.py data/test_inputs.jsonl --output reports/results.json
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import requests


API_URL = "http://localhost:8000"


def check_api_health() -> bool:
    """检查 API 服务是否运行 / Check if API server is running"""
    try:
        response = requests.get("{}/health".format(API_URL), timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def load_test_cases(filepath: str) -> List[Dict[str, Any]]:
    """加载测试用例 / Load test cases"""
    cases = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
                # Only require user_input field
                if "user_input" not in case:
                    print("Warning: Line {} missing 'user_input' field".format(line_num))
                    continue
                cases.append(case)
            except json.JSONDecodeError as e:
                print("Warning: Line {} invalid JSON: {}".format(line_num, e))
                continue
    return cases


def run_test_case(case: Dict[str, Any], delay: float = 0.5) -> Dict[str, Any]:
    """运行单个测试用例 / Run single test case"""
    try:
        # Send chat request
        response = requests.post(
            "{}/chat".format(API_URL),
            json={
                "user_input": case["user_input"],
                "metadata": case.get("metadata", {})
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        # Delay before next request
        time.sleep(delay)
        
        return {
            "success": True,
            "interaction_id": result["interaction_id"],
            "user_input": case["user_input"],
            "response_text": result["response_text"],
            "refusal": result.get("refusal", False),
            "timestamp": result.get("timestamp", "")
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "user_input": case["user_input"],
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "user_input": case["user_input"],
            "error": "Unexpected error: {}".format(str(e))
        }


def print_summary(results: List[Dict[str, Any]]) -> None:
    """打印测试摘要 / Print test summary"""
    total = len(results)
    success = sum(1 for r in results if r["success"])
    failed = total - success
    
    print("\n" + "=" * 60)
    print("Test Summary / 测试摘要")
    print("=" * 60)
    print("Total Test Cases / 总测试数: {}".format(total))
    print("Successful / 成功: {}".format(success))
    print("Failed / 失败: {}".format(failed))
    print("Success Rate / 成功率: {:.1f}%".format(success/total*100))
    
    if failed > 0:
        print("\nFailed Cases / 失败用例:")
        for i, r in enumerate(results, 1):
            if not r["success"]:
                print("  {}. {}...".format(i, r['user_input'][:50]))
                print("     Error: {}".format(r['error']))
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="ZenAi Batch Test Script / ZenAi 批量测试脚本"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Input JSONL file with test cases / 测试用例 JSONL 文件"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file for results / 结果输出 JSON 文件"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds / 请求间隔（秒）"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL / API 基础地址"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output / 打印详细输出"
    )
    
    args = parser.parse_args()
    
    global API_URL
    API_URL = args.api_url
    
    # Check if API server is running
    print("=" * 60)
    print("ZenAi Batch Test / ZenAi 批量测试")
    print("=" * 60)
    print("\nChecking API server at: {}".format(API_URL))
    
    if not check_api_health():
        print("Error: API server is not running at {}".format(API_URL))
        print("Please start the main API server first:")
        print("  bash start.sh")
        print("  or: python src/api/app.py")
        sys.exit(1)
    
    print("API server is running\n")
    
    # Check if input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        print("Error: Input file not found: {}".format(input_path))
        sys.exit(1)
    
    # Load test cases
    print("Loading test cases from: {}".format(input_path))
    test_cases = load_test_cases(str(input_path))
    
    if not test_cases:
        print("Error: No valid test cases found")
        sys.exit(1)
    
    print("Loaded {} test cases / 加载了 {} 个测试用例".format(len(test_cases), len(test_cases)))
    print("Delay between requests: {}s / 请求间隔: {}秒".format(args.delay, args.delay))
    print()
    
    # Run tests
    results = []
    for i, case in enumerate(test_cases, 1):
        user_input = case["user_input"]
        display_input = user_input[:50] + "..." if len(user_input) > 50 else user_input
        
        print("[{}/{}] Testing: {}".format(i, len(test_cases), display_input))
        
        result = run_test_case(case, delay=args.delay)
        results.append(result)
        
        if args.verbose:
            if result["success"]:
                print("  Success - ID: {}".format(result['interaction_id']))
                print("    Response: {}...".format(result['response_text'][:80]))
            else:
                print("  Failed - {}".format(result['error']))
        elif result["success"]:
            print("  Success")
        else:
            print("  Failed: {}".format(result['error']))
    
    # Print summary
    print_summary(results)
    
    # Save results if output file specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "test_file": str(input_path),
                "total_cases": len(test_cases),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        print("\nResults saved to: {}".format(output_path))
    
    # Exit with error code if any tests failed
    failed_count = sum(1 for r in results if not r["success"])
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
