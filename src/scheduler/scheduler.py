from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

from apscheduler.schedulers.background import BackgroundScheduler

from ..orator import ZenAiOrator
from ..storage import ResonanceArchive
from ..trainer import ZenAiTrainer


@dataclass
class IterationConfig:
    """
    Configuration for iteration scheduling.
    
    DEPRECATED: Use SchedulerConfig from src.config instead.
    This class is kept for backward compatibility.
    """
    time_window_hours: int
    min_interactions: int
    check_interval_minutes: int
    
    @classmethod
    def from_config(cls, config) -> IterationConfig:
        """Create IterationConfig from SchedulerConfig"""
        return cls(
            time_window_hours=config.time_window_hours,
            min_interactions=config.min_interactions,
            check_interval_minutes=config.check_interval_minutes,
        )


class IterationScheduler:
    """
    Automatic iteration scheduler for ZenAi system.
    
    Pure coordination layer - delegates computation to Trainer (修炼者).
    纯调度层 - 将计算委托给修炼者。
    
    Responsibilities:
    - Monitor interaction accumulation
    - Trigger iterations at appropriate times
    - Coordinate Trainer and Orator
    - Handle safety checks and system control
    
    Does NOT compute metrics or evolve prompts - that's Trainer's job.
    不计算指标或演化提示词 - 那是修炼者的职责。
    """

    def __init__(
        self,
        trainer: ZenAiTrainer,
        orator: ZenAiOrator,
        archive: ResonanceArchive,
        config: IterationConfig,
    ):
        if config is None:
            raise ValueError(
                "IterationConfig is required. "
                "All configuration must be explicitly provided."
            )
        self.trainer = trainer
        self.orator = orator
        self.archive = archive
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.current_iteration_start: datetime | None = None

    def start(self) -> None:
        """Start the scheduler"""
        # Initialize first iteration
        self._start_new_iteration()
        
        # Schedule periodic checks
        self.scheduler.add_job(
            self._check_iteration_trigger,
            "interval",
            minutes=self.config.check_interval_minutes,
            id="iteration_check",
        )
        
        self.scheduler.start()
        print(f"Scheduler started. Checking every {self.config.check_interval_minutes} minutes.")

    def stop(self) -> None:
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("Scheduler stopped.")

    def should_trigger_iteration(self) -> bool:
        """
        Check if conditions are met to trigger an iteration.
        
        Conditions:
        - Time window elapsed (default 24 hours)
        - Minimum interactions met (default 1000)
        """
        if not self.current_iteration_start:
            return True

        # Check time window
        elapsed = datetime.utcnow() - self.current_iteration_start
        time_window = timedelta(hours=self.config.time_window_hours)
        time_elapsed = elapsed >= time_window

        # Check interaction count
        interaction_count = self.archive.get_interaction_count(
            start_time=self.current_iteration_start,
        )
        min_interactions_met = interaction_count >= self.config.min_interactions

        return time_elapsed and min_interactions_met

    def run_iteration_cycle(self) -> None:
        """
        Execute iteration cycle by coordinating Trainer and Orator.
        
        Simplified flow - Scheduler only coordinates, Trainer does the work.
        简化流程 - 调度器只协调，修炼者完成实际工作。
        
        Steps:
        1. Check safety conditions
        2. Create iteration record
        3. Delegate to Trainer for computation and evolution
        4. Complete iteration in archive
        5. Check safety conditions again
        6. Start next iteration
        """
        print(f"\n{'='*50}")
        print(f"[Scheduler] Starting iteration cycle at {datetime.utcnow()}")
        print(f"{'='*50}\n")

        # Check if system is killed
        if self.archive.is_killed():
            print("[Scheduler] System is killed. Stopping scheduler.")
            self.stop()
            return

        # Quick check for interactions
        current_interactions = self.archive.load_interactions_by_time_window(
            start_time=self.current_iteration_start or datetime.utcnow(),
        )

        if not current_interactions:
            print("[Scheduler] No interactions found in current window. Skipping iteration.")
            return

        # Create iteration record
        iteration_id = self.archive.create_iteration(
            start_time=self.current_iteration_start or datetime.utcnow(),
            prompt_version=self.orator.get_current_prompt_version(),
        )

        print(f"[Scheduler] Created iteration {iteration_id}")

        try:
            # Delegate to Trainer (修炼者) for computation and evolution
            result = self.trainer.run_iteration_cycle(
                iteration_id=iteration_id,
                start_time=self.current_iteration_start or datetime.utcnow(),
                end_time=datetime.utcnow(),
            )

            # Complete iteration in archive
            self.archive.complete_iteration(
                iteration_id=iteration_id,
                end_time=datetime.utcnow(),
                total_interactions=result.metrics.total_responses,
                state=result.state.value,
                metrics=result.metrics.to_dict(),
            )

            print(f"[Scheduler] Iteration {iteration_id} completed with state: {result.state.value}")

            # Check safety conditions
            from ..safety import SafetyController
            safety = SafetyController(self.archive)
            if safety.should_kill(result.state, result.metrics):
                print("\n[Scheduler] !!! KILL CONDITION MET !!!")
                print("[Scheduler] System will be terminated.")
                safety.kill()
                self.stop()
                return

            # Start next iteration
            self._start_new_iteration()

        except Exception as exc:
            print(f"[Scheduler] ERROR during iteration cycle: {exc}")
            import traceback
            traceback.print_exc()
            # Mark iteration as failed but don't crash the scheduler
            self.archive.complete_iteration(
                iteration_id=iteration_id,
                end_time=datetime.utcnow(),
                total_interactions=len(current_interactions),
                state="dead",
                metrics={},
            )

        print(f"\n{'='*50}")
        print(f"[Scheduler] Iteration cycle completed at {datetime.utcnow()}")
        print(f"{'='*50}\n")

    def _check_iteration_trigger(self) -> None:
        """Periodic check to see if iteration should be triggered"""
        if self.should_trigger_iteration():
            print("\nIteration trigger conditions met. Starting iteration cycle...")
            self.run_iteration_cycle()

    def _start_new_iteration(self) -> None:
        """Initialize a new iteration period"""
        self.current_iteration_start = datetime.utcnow()
        print(f"New iteration period started at {self.current_iteration_start}")

    def force_iteration(self) -> None:
        """Manually trigger an iteration cycle"""
        print("Forcing iteration cycle...")
        self.run_iteration_cycle()
