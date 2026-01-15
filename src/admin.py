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
    print(f"\nTimestamp: {metrics.timestamp}")
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
    }
    
    return commands[args.command](args) or 0


if __name__ == "__main__":
    sys.exit(main())
