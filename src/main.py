#!/usr/bin/env python3
"""
ZenAi Main Entry Point / ZenAi 主入口

Starts both the Orator API and Trainer scheduler.
启动布道者 API 和修炼者调度器。
"""
from __future__ import annotations

import argparse
import signal
import sys
import threading
from pathlib import Path

import uvicorn

from .api.app import app, app_state
from .config import load_config
from .scheduler import IterationConfig, IterationScheduler


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser with defaults from config.yml"""
    # Load config for defaults
    config = load_config()
    
    parser = argparse.ArgumentParser(
        description="ZenAi System - Start Orator API and Trainer Scheduler"
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
        help=f"Path to SQLite database file (default: {config.paths.database})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API server host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port",
    )
    parser.add_argument(
        "--iteration-hours",
        type=int,
        default=None,
        help=f"[DEPRECATED] No longer used - iterations trigger on interaction count only",
    )
    parser.add_argument(
        "--min-interactions",
        type=int,
        default=None,
        help=f"Trigger iteration when this many interactions accumulated (default: {config.scheduler.min_interactions})",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=None,
        help=f"Scheduler check interval in minutes (default: {config.scheduler.check_interval_minutes})",
    )
    parser.add_argument(
        "--no-scheduler",
        action="store_true",
        help="Run API only without scheduler",
    )
    return parser


def start_scheduler(
    trainer,
    orator,
    archive,
    config: IterationConfig,
) -> IterationScheduler:
    """Start iteration scheduler in background"""
    scheduler = IterationScheduler(
        trainer=trainer,
        orator=orator,
        archive=archive,
        config=config,
    )
    scheduler.start()
    return scheduler


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    
    # Load configuration (command-line args have priority)
    config = load_config(args.config)
    
    # Apply command-line overrides
    db_path = args.db_path if args.db_path else config.paths.database
    iteration_hours = args.iteration_hours if args.iteration_hours else config.scheduler.time_window_hours
    min_interactions = args.min_interactions if args.min_interactions else config.scheduler.min_interactions
    check_interval = args.check_interval if args.check_interval else config.scheduler.check_interval_minutes

    print("=" * 60)
    print("ZenAi System Starting / ZenAi 系统启动中")
    print("=" * 60)
    print(f"Config: {args.config}")
    print(f"Database: {db_path}")
    print(f"API Server: http://{args.host}:{args.port}")
    print(f"Iteration Trigger: {min_interactions} interactions (pure count-based)")
    print(f"Check Interval: {check_interval} minutes")
    print(f"Scheduler: {'Enabled' if not args.no_scheduler else 'Disabled'}")
    print("=" * 60)

    scheduler = None

    def signal_handler(sig, frame):
        """Handle graceful shutdown"""
        print("\n\nShutting down ZenAi system...")
        if scheduler:
            scheduler.stop()
        print("Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start scheduler in background if enabled
    if not args.no_scheduler:
        # We need to wait for app startup to get all components
        def start_scheduler_after_startup():
            import time
            time.sleep(2)  # Wait for API startup
            if app_state.archive and app_state.trainer and app_state.orator:
                scheduler_config = IterationConfig(
                    time_window_hours=iteration_hours,
                    min_interactions=min_interactions,
                    check_interval_minutes=check_interval,
                )
                nonlocal scheduler
                scheduler = start_scheduler(
                    app_state.trainer,
                    app_state.orator,
                    app_state.archive,
                    scheduler_config,
                )
                print(f"\n✓ Scheduler started successfully!")
            else:
                print("\n✗ Scheduler startup failed: components not initialized")

        scheduler_thread = threading.Thread(
            target=start_scheduler_after_startup,
            daemon=True,
        )
        scheduler_thread.start()

    # Start API server (blocking)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
