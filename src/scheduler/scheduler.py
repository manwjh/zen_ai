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
    
    Philosophy:
    - Trigger based on interaction accumulation, not time
    - The Trainer practices when ready, not on a schedule
    - 基于交互积累触发，而非时间
    - 修炼者在准备好时修炼，而非按时间表
    
    Responsibilities:
    - Monitor interaction accumulation
    - Trigger iterations when sufficient data accumulated
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
        # Check immediately if conditions are already met
        # 如果启动时条件已满足，立即触发第一次迭代
        if self.should_trigger_iteration():
            print("\n[Scheduler] Sufficient unassigned interactions found at startup. Triggering first iteration immediately...")
            self.run_iteration_cycle()
        
        # Schedule periodic checks
        self.scheduler.add_job(
            self._check_iteration_trigger,
            "interval",
            minutes=self.config.check_interval_minutes,
            id="iteration_check",
        )
        
        self.scheduler.start()
        print(f"[Scheduler] Started. Checking every {self.config.check_interval_minutes} minutes.")

    def stop(self) -> None:
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("Scheduler stopped.")

    def should_trigger_iteration(self) -> bool:
        """
        Check if conditions are met to trigger an iteration.
        
        Pure approach: Trigger when sufficient unassigned interactions accumulated.
        纯粹方法：当积累足够未分配的交互数据时触发。
        
        Condition:
        - Minimum unassigned interactions met (default 100)
        
        The Trainer practices when ready, not on a fixed schedule.
        修炼者在准备好时修炼，而非按固定时间表。
        """
        # Count unassigned interactions (not yet processed by any iteration)
        unassigned = self.archive.load_unassigned_interactions()
        
        return len(unassigned) >= self.config.min_interactions

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

        # Load unassigned interactions (not yet processed by any iteration)
        from ..storage.database import InteractionRecord
        with self.archive.create_session() as session:
            records = (
                session.query(InteractionRecord)
                .filter_by(iteration_id=None)
                .order_by(InteractionRecord.timestamp)
                .all()
            )
            
            if not records:
                print("[Scheduler] No unassigned interactions found. Skipping iteration.")
                return
            
            print(f"[Scheduler] Found {len(records)} unassigned interactions")
            
            # Extract data we need from records before session closes
            record_ids = [r.id for r in records]
            start_time = records[0].timestamp  # Already sorted by timestamp
            end_time = records[-1].timestamp
        
        # Convert to Interaction objects for processing (outside session)
        unassigned_interactions = self.archive.load_unassigned_interactions()
        
        iteration_id = self.archive.create_iteration(
            start_time=start_time,
            prompt_version=self.orator.get_current_prompt_version(),
        )

        print(f"[Scheduler] Created iteration {iteration_id}")

        try:
            # Assign unassigned interactions to this iteration
            self.archive.assign_interactions_to_iteration(
                interaction_ids=record_ids,
                iteration_id=iteration_id,
            )
            print(f"[Scheduler] Assigned {len(record_ids)} interactions to iteration {iteration_id}")

            # Delegate to Trainer (修炼者) for computation and evolution
            result = self.trainer.run_iteration_cycle(
                iteration_id=iteration_id,
                start_time=start_time,
                end_time=end_time,
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

            # No need to call _start_new_iteration() - we use unassigned interactions

        except Exception as exc:
            print(f"[Scheduler] ERROR during iteration cycle: {exc}")
            import traceback
            traceback.print_exc()
            # Mark iteration as failed but don't crash the scheduler
            self.archive.complete_iteration(
                iteration_id=iteration_id,
                end_time=datetime.utcnow(),
                total_interactions=len(unassigned_interactions),
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

    def force_iteration(self) -> None:
        """Manually trigger an iteration cycle"""
        print("Forcing iteration cycle...")
        self.run_iteration_cycle()
