#!/usr/bin/env python3
"""
ZenAi Admin Tool / ZenAi 管理工具

Administrative commands for ZenAi system.
ZenAi 系统管理命令。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import load_config
from .core.models import PromptPolicy
from .core.prompt import render_prompt
from .llm.config import load_llm_config
from .monitoring import SystemMonitor
from .orator import ZenAiOrator
from .safety import SafetyController
from .storage import ResonanceArchive


def cmd_status(args):
    """Show system status"""
    archive = ResonanceArchive(db_path=args.db_path)
    monitor = SystemMonitor(archive)
    
    metrics = monitor.get_current_metrics()
    health = monitor.check_health()
    
    print("\n" + "=" * 60)
    print("ZenAi System Status / ZenAi 系统状态")
    print("=" * 60)
    print(f"\nSystem Version: {__version__}")
    print(f"Timestamp: {metrics.timestamp}")
    print(f"\nSystem State / 系统状态:")
    print(f"  Current State: {metrics.current_state}")
    print(f"  Prompt Version: {metrics.prompt_version}")
    print(f"  Iteration ID: {metrics.current_iteration_id}")
    print(f"  Frozen: {metrics.is_frozen}")
    print(f"  Killed: {metrics.is_killed}")
    
    print(f"\nInteractions / 交互统计:")
    print(f"  Total: {metrics.total_interactions}")
    print(f"  Last 24h: {metrics.last_24h_interactions}")
    print(f"  Total Iterations: {metrics.total_iterations}")
    
    print(f"\nHealth / 健康状态: {health.status.upper()}")
    if health.issues:
        print(f"\nIssues / 问题:")
        for issue in health.issues:
            print(f"  - {issue}")
    if health.recommendations:
        print(f"\nRecommendations / 建议:")
        for rec in health.recommendations:
            print(f"  - {rec}")
    
    if metrics.latest_metrics:
        print(f"\nLatest Metrics / 最新指标:")
        for key, value in metrics.latest_metrics.items():
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60 + "\n")


def cmd_freeze(args):
    """Freeze system evolution"""
    archive = ResonanceArchive(db_path=args.db_path)
    safety = SafetyController(archive)
    safety.freeze()
    print("System evolution FROZEN. / 系统演化已冻结。")


def cmd_unfreeze(args):
    """Unfreeze system evolution"""
    archive = ResonanceArchive(db_path=args.db_path)
    safety = SafetyController(archive)
    safety.unfreeze()
    print("System evolution UNFROZEN. / 系统演化已解冻。")


def cmd_rollback(args):
    """Rollback to previous prompt version"""
    archive = ResonanceArchive(db_path=args.db_path)
    safety = SafetyController(archive)
    
    try:
        new_version = safety.rollback(args.version)
        print(f"Rolled back to version {args.version if args.version else 'previous'}")
        print(f"New version {new_version} created with rollback prompt.")
    except Exception as e:
        print(f"Rollback failed: {e}")
        return 1


def cmd_kill(args):
    """Kill the system"""
    archive = ResonanceArchive(db_path=args.db_path)
    safety = SafetyController(archive)
    
    if not args.confirm:
        print("ERROR: Must use --confirm to kill the system")
        return 1
    
    safety.kill()
    print("System KILLED. / 系统已终止。")


def cmd_history(args):
    """Show iteration history"""
    archive = ResonanceArchive(db_path=args.db_path)
    monitor = SystemMonitor(archive)
    
    history = monitor.get_iteration_history(n=args.limit)
    
    print("\n" + "=" * 60)
    print(f"Iteration History / 迭代历史 (Last {args.limit})")
    print("=" * 60)
    
    for item in history:
        print(f"\nIteration {item['id']}:")
        print(f"  Time: {item['start_time']} -> {item['end_time']}")
        print(f"  State: {item['state']}")
        print(f"  Interactions: {item['total_interactions']}")
        print(f"  Prompt Version: {item['prompt_version']}")
        if args.verbose and item['metrics']:
            print(f"  Metrics:")
            for key, value in item['metrics'].items():
                print(f"    {key}: {value}")
    
    print("\n" + "=" * 60 + "\n")


def cmd_prompts(args):
    """Show prompt evolution history"""
    archive = ResonanceArchive(db_path=args.db_path)
    monitor = SystemMonitor(archive)
    
    history = monitor.get_prompt_evolution_history()
    
    print("\n" + "=" * 60)
    print("Prompt Evolution History / 提示词演化历史")
    print("=" * 60)
    
    for item in history:
        print(f"\nVersion {item['version']}:")
        print(f"  Timestamp: {item['timestamp']}")
        print(f"  Actions: {item['actions']}")
        print(f"  Policy: {item['policy']}")
    
    print("\n" + "=" * 60 + "\n")


def cmd_export(args):
    """Export metrics to JSON"""
    archive = ResonanceArchive(db_path=args.db_path)
    monitor = SystemMonitor(archive)
    
    monitor.export_metrics_json(args.output)
    print(f"Metrics exported to {args.output}")


def cmd_gathas(args):
    """View gatha history with explanations"""
    archive = ResonanceArchive(db_path=args.db_path)
    gathas = archive.get_all_gathas(limit=args.limit)
    
    if not gathas:
        print("\n" + "=" * 60)
        print("No gathas found. / 未找到偈子。")
        print("=" * 60 + "\n")
        print("Gathas are generated after each iteration cycle.")
        print("偈子在每次迭代周期后生成。")
        return
    
    print("\n" + "=" * 60)
    print("Gatha History / 偈子历史")
    print("=" * 60 + "\n")
    
    for g in gathas:
        iteration_id = g["iteration_id"]
        end_time = g.get("end_time") or "N/A"
        state = g["state"]
        gatha = g.get("gatha", "")
        explanation = g.get("explanation", "")
        metrics = g["metrics"]
        
        print(f"[Iteration {iteration_id}] {end_time}")
        print(f"State: {state}", end="")
        
        if metrics:
            rr = metrics.get("resonance_ratio", 0)
            rd = metrics.get("rejection_density", 0)
            print(f" | RR: {rr:.2%} | RD: {rd:.2%}", end="")
        
        q_count = g.get("questions_count", 0)
        gen_time = g.get("generation_time", 0)
        print(f" | Questions: {q_count} | Gen: {gen_time:.2f}s")
        
        print("\n【偈子】")
        print(gatha)
        
        if explanation and args.verbose:
            print("\n【解释稿】")
            print(explanation)
        elif explanation:
            # Show truncated explanation
            if len(explanation) > 100:
                print(f"\n【解释稿】{explanation[:100]}...")
            else:
                print(f"\n【解释稿】{explanation}")
            print("(使用 --verbose 查看完整解释)")
        
        print()
        print("─" * 60 + "\n")


def cmd_iterate(args):
    """Manually trigger an iteration cycle"""
    from datetime import datetime, timedelta
    from .config import load_config
    from .trainer import ZenAiTrainer
    from .orator import ZenAiOrator
    from .llm.config import load_llm_config
    
    print("\n" + "=" * 60)
    print("Manual Iteration Trigger / 手动触发迭代")
    print("=" * 60 + "\n")
    
    # Load configuration
    config = load_config(args.config)
    db_path = args.db_path or config.paths.database
    
    # Initialize components
    archive = ResonanceArchive(db_path=db_path)
    
    # Check interaction count
    total_interactions = archive.get_interaction_count()
    print(f"Total interactions in database: {total_interactions}")
    
    if total_interactions < config.scheduler.min_interactions:
        print(f"⚠️  Insufficient interactions: {total_interactions} < {config.scheduler.min_interactions}")
        print("Cannot trigger iteration. More data needed.")
        return 1
    
    # Get latest iteration
    latest_iteration = archive.get_latest_iteration()
    if latest_iteration:
        print(f"Latest iteration: {latest_iteration.id} at {latest_iteration.end_time}")
        start_time = latest_iteration.end_time
    else:
        print("No previous iterations. This will be the first iteration.")
        start_time = datetime.utcnow() - timedelta(days=365)  # Include all historical data
    
    # Count interactions since last iteration
    interactions_since = archive.get_interaction_count(start_time=start_time)
    print(f"Interactions since last iteration: {interactions_since}")
    
    if interactions_since < config.scheduler.min_interactions:
        print(f"⚠️  Insufficient new interactions: {interactions_since} < {config.scheduler.min_interactions}")
        if not args.force:
            print("Use --force to trigger anyway.")
            return 1
        print("Forcing iteration anyway (--force)...")
    
    # Initialize Trainer and Orator
    print("\nInitializing Trainer and Orator...")
    trainer = ZenAiTrainer.from_config(archive, config)
    
    llm_config = load_llm_config()
    orator = ZenAiOrator(llm_config=llm_config, archive=archive)
    
    # Create iteration record
    print("\nCreating iteration record...")
    iteration_id = archive.create_iteration(
        start_time=start_time,
        prompt_version=orator.get_current_prompt_version(),
    )
    
    print(f"Created iteration {iteration_id}")
    
    try:
        # Run iteration cycle
        print("\nRunning iteration cycle...")
        result = trainer.run_iteration_cycle(
            iteration_id=iteration_id,
            start_time=start_time,
            end_time=datetime.utcnow(),
        )
        
        # Complete iteration
        archive.complete_iteration(
            iteration_id=iteration_id,
            end_time=datetime.utcnow(),
            total_interactions=result.metrics.total_responses,
            state=result.state.value,
            metrics=result.metrics.to_dict(),
        )
        
        print(f"\n✓ Iteration {iteration_id} completed successfully!")
        print(f"  State: {result.state.value}")
        print(f"  Total interactions: {result.metrics.total_responses}")
        print(f"  Resonance ratio: {result.metrics.resonance_ratio:.2%}")
        
        if result.new_prompt_version:
            print(f"  New prompt version: {result.new_prompt_version}")
        
        print("\n" + "=" * 60 + "\n")
        return 0
        
    except Exception as e:
        print(f"\n✗ Iteration failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Mark as failed
        archive.complete_iteration(
            iteration_id=iteration_id,
            end_time=datetime.utcnow(),
            total_interactions=interactions_since,
            state="dead",
            metrics={},
        )
        return 1


def build_parser() -> argparse.ArgumentParser:
    # Load config to get database path (no hardcoded defaults)
    config = load_config()
    
    parser = argparse.ArgumentParser(
        description="ZenAi Admin Tool / ZenAi 管理工具"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help=f"Path to SQLite database (default: {config.paths.database})",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # status
    subparsers.add_parser("status", help="Show system status")
    
    # freeze
    subparsers.add_parser("freeze", help="Freeze system evolution")
    
    # unfreeze
    subparsers.add_parser("unfreeze", help="Unfreeze system evolution")
    
    # rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to previous version")
    rollback_parser.add_argument(
        "--version",
        type=int,
        default=None,
        help="Target version (default: previous)",
    )
    
    # kill
    kill_parser = subparsers.add_parser("kill", help="Kill the system")
    kill_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm system termination",
    )
    
    # history
    history_parser = subparsers.add_parser("history", help="Show iteration history")
    history_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of iterations to show",
    )
    history_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed metrics",
    )
    
    # prompts
    subparsers.add_parser("prompts", help="Show prompt evolution history")
    
    # export
    export_parser = subparsers.add_parser("export", help="Export metrics to JSON")
    export_parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output JSON file path",
    )
    
    # gathas
    gathas_parser = subparsers.add_parser("gathas", help="View gatha history with explanations")
    gathas_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of gathas to show (default: 10)",
    )
    gathas_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full explanation text",
    )
    
    # iterate
    iterate_parser = subparsers.add_parser("iterate", help="Manually trigger an iteration cycle")
    iterate_parser.add_argument(
        "--force",
        action="store_true",
        help="Force iteration even if insufficient new interactions",
    )
    
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Load configuration and apply command-line overrides
    config = load_config(args.config)
    if not args.db_path:
        args.db_path = config.paths.database
    
    commands = {
        "status": cmd_status,
        "freeze": cmd_freeze,
        "unfreeze": cmd_unfreeze,
        "rollback": cmd_rollback,
        "kill": cmd_kill,
        "history": cmd_history,
        "prompts": cmd_prompts,
        "export": cmd_export,
        "gathas": cmd_gathas,
        "iterate": cmd_iterate,
    }
    
    return commands[args.command](args) or 0


if __name__ == "__main__":
    sys.exit(main())
