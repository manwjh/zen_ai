from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..core.models import IterationMetrics, SystemState
from ..storage import ResonanceArchive


@dataclass
class SafetyThresholds:
    """
    Thresholds for safety mechanisms.
    
    DEPRECATED: Use SafetyThresholdsConfig from src.config instead.
    This class is kept for backward compatibility.
    """
    kill_consecutive_collapsing: int
    kill_consecutive_mute: int
    kill_min_rr: float
    kill_max_rd: float
    kill_max_sci: float
    
    @classmethod
    def from_config(cls, config) -> SafetyThresholds:
        """Create SafetyThresholds from SafetyThresholdsConfig"""
        return cls(
            kill_consecutive_collapsing=config.kill_consecutive_collapsing,
            kill_consecutive_mute=config.kill_consecutive_mute,
            kill_min_rr=config.kill_min_rr,
            kill_max_rd=config.kill_max_rd,
            kill_max_sci=config.kill_max_sci,
        )


class SafetyController:
    """
    Safety mechanisms for ZenAi system.
    
    Implements three safety buttons from design spec:
    - Freeze: Pause evolution, continue execution
    - Rollback: Revert to previous stable prompt
    - Kill: Terminate system permanently
    """

    def __init__(
        self,
        archive: ResonanceArchive,
        thresholds: SafetyThresholds | None = None,
    ):
        if thresholds is None:
            # Load from config if not provided
            from ..config import load_config
            config = load_config()
            thresholds = SafetyThresholds.from_config(config.safety_thresholds)
        self.archive = archive
        self.thresholds = thresholds

    # ========================================
    # Freeze Mechanism
    # ========================================

    def freeze(self) -> None:
        """
        Freeze system evolution.
        
        When frozen:
        - Orator continues to respond
        - Interactions are still recorded
        - Metrics are computed
        - Prompts do NOT evolve
        """
        self.archive.set_status("frozen", "true")
        self.archive.set_status("frozen_at", datetime.utcnow().isoformat())
        print("System FROZEN. Evolution paused.")

    def unfreeze(self) -> None:
        """Unfreeze system evolution"""
        self.archive.set_status("frozen", "false")
        print("System UNFROZEN. Evolution resumed.")

    def is_frozen(self) -> bool:
        """Check if system is frozen"""
        return self.archive.is_frozen()

    # ========================================
    # Rollback Mechanism
    # ========================================

    def rollback(self, target_version: int | None = None) -> int:
        """
        Rollback to a previous prompt version.
        
        If target_version is None, rolls back to the previous version.
        Returns the version that was rolled back to.
        """
        all_versions = self.archive.get_all_prompt_versions()
        if not all_versions:
            raise RuntimeError("No prompt versions available for rollback")

        current_version = max(all_versions)
        
        if target_version is None:
            # Rollback to previous version
            if len(all_versions) < 2:
                raise RuntimeError("No previous version to rollback to")
            target_version = sorted(all_versions)[-2]
        
        if target_version not in all_versions:
            raise ValueError(f"Target version {target_version} does not exist")
        
        if target_version >= current_version:
            raise ValueError(f"Cannot rollback to version {target_version} (current: {current_version})")

        # Load target prompt
        target_prompt = self.archive.load_prompt(target_version)
        if not target_prompt:
            raise RuntimeError(f"Failed to load prompt version {target_version}")

        # Create new version with rollback marker
        new_version = current_version + 1
        self.archive.save_prompt(
            version=new_version,
            prompt_text=target_prompt.prompt_text,
            policy=target_prompt.policy,
            actions=[f"rollback_to_v{target_version}"],
        )

        self.archive.set_status("last_rollback", datetime.utcnow().isoformat())
        self.archive.set_status("rollback_from", str(current_version))
        self.archive.set_status("rollback_to", str(target_version))

        print(f"Rolled back from version {current_version} to {target_version}")
        print(f"New version {new_version} created with rollback prompt")

        return new_version

    # ========================================
    # Kill Mechanism
    # ========================================

    def kill(self) -> None:
        """
        Permanently terminate the system.
        
        When killed:
        - Orator stops responding (returns error)
        - No new interactions recorded
        - No evolution occurs
        - Data is preserved
        - Instance is closed
        """
        self.archive.set_status("killed", "true")
        self.archive.set_status("killed_at", datetime.utcnow().isoformat())
        print("\n" + "="*50)
        print("SYSTEM KILLED")
        print("Instance terminated permanently.")
        print("Data preserved in archive.")
        print("="*50 + "\n")

    def is_killed(self) -> bool:
        """Check if system has been killed"""
        return self.archive.is_killed()

    # ========================================
    # Automatic Kill Conditions
    # ========================================

    def should_kill(
        self,
        current_state: SystemState,
        current_metrics: IterationMetrics,
    ) -> bool:
        """
        Determine if system should be automatically killed.
        
        Kill conditions:
        - N consecutive COLLAPSING iterations
        - N consecutive MUTE iterations
        - Resonance ratio below threshold
        - Rejection density above threshold
        - Semantic collapse above threshold
        """
        # Check extreme metric values
        if current_metrics.resonance_ratio <= self.thresholds.kill_min_rr:
            print(f"Kill condition: RR below {self.thresholds.kill_min_rr}")
            return True

        if current_metrics.rejection_density >= self.thresholds.kill_max_rd:
            print(f"Kill condition: RD above {self.thresholds.kill_max_rd}")
            return True

        if current_metrics.semantic_collapse_index >= self.thresholds.kill_max_sci:
            print(f"Kill condition: SCI above {self.thresholds.kill_max_sci}")
            return True

        # Check consecutive bad states
        if current_state == SystemState.DEAD:
            print("Kill condition: State is DEAD")
            return True

        # Check recent iteration history
        recent_states = self._get_recent_states(n=5)
        
        consecutive_collapsing = self._count_consecutive_state(
            recent_states,
            SystemState.COLLAPSING,
        )
        if consecutive_collapsing >= self.thresholds.kill_consecutive_collapsing:
            print(f"Kill condition: {consecutive_collapsing} consecutive COLLAPSING iterations")
            return True

        consecutive_mute = self._count_consecutive_state(
            recent_states,
            SystemState.MUTE,
        )
        if consecutive_mute >= self.thresholds.kill_consecutive_mute:
            print(f"Kill condition: {consecutive_mute} consecutive MUTE iterations")
            return True

        return False

    def _get_recent_states(self, n: int = 5) -> list[SystemState]:
        """Get the most recent N iteration states"""
        states: list[SystemState] = []
        iteration_count = self.archive.get_iteration_count()
        
        for i in range(max(1, iteration_count - n + 1), iteration_count + 1):
            iteration = self.archive.get_iteration(i)
            if iteration:
                try:
                    states.append(SystemState(iteration.state))
                except ValueError:
                    pass  # Skip invalid states
        
        return states

    def _count_consecutive_state(
        self,
        states: list[SystemState],
        target_state: SystemState,
    ) -> int:
        """Count consecutive occurrences of target_state from the end"""
        count = 0
        for state in reversed(states):
            if state == target_state:
                count += 1
            else:
                break
        return count

    # ========================================
    # Status Reporting
    # ========================================

    def get_safety_status(self) -> dict[str, Any]:
        """Get current safety status"""
        from typing import Any
        
        return {
            "frozen": self.is_frozen(),
            "killed": self.is_killed(),
            "frozen_at": self.archive.get_status("frozen_at"),
            "killed_at": self.archive.get_status("killed_at"),
            "last_rollback": self.archive.get_status("last_rollback"),
            "rollback_from": self.archive.get_status("rollback_from"),
            "rollback_to": self.archive.get_status("rollback_to"),
        }
