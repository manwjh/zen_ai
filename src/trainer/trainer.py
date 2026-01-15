from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from ..core import (
    EvolutionAction,
    EvolutionRules,
    Interaction,
    IterationMetrics,
    PromptPolicy,
    SystemState,
    compute_metrics,
    evaluate_state,
    evolve_prompt,
)
from ..core.state import StateThresholds
from ..storage import ResonanceArchive


@dataclass
class TrainerIterationResult:
    """Result of a Trainer iteration cycle"""
    iteration_id: int
    state: SystemState
    metrics: IterationMetrics
    evolution_actions: list[EvolutionAction]
    new_prompt_version: int | None


@dataclass
class ZenAiTrainer:
    """
    ZenAi Trainer (修炼者) - Silent practice through computation.
    
    Embodies the core identity through algorithms and metrics.
    通过算法和指标体现核心身份。
    
    Responsibilities:
    - Compute metrics from interactions
    - Evaluate system state
    - Evolve prompt policy
    - NO direct interaction with users (that's Orator's job)
    
    Represents "不立文字" (no establishment of words) - the Zen principle
    of wordless practice through pure computation.
    """
    
    archive: ResonanceArchive
    thresholds: StateThresholds
    rules: EvolutionRules
    
    @classmethod
    def from_config(cls, archive: ResonanceArchive, config) -> ZenAiTrainer:
        """Create Trainer from configuration"""
        from ..core.state import StateThresholds
        from ..core.evolution import EvolutionRules
        
        return cls(
            archive=archive,
            thresholds=StateThresholds(
                stable_min_rr=config.state_thresholds.stable_min_rr,
                stable_max_rd=config.state_thresholds.stable_max_rd,
                stable_min_rld=config.state_thresholds.stable_min_rld,
                stable_max_rf=config.state_thresholds.stable_max_rf,
                stable_max_sci=config.state_thresholds.stable_max_sci,
                drifting_rr_drop=config.state_thresholds.drifting_rr_drop,
                collapsing_rr=config.state_thresholds.collapsing_rr,
                collapsing_rd=config.state_thresholds.collapsing_rd,
                collapsing_sci=config.state_thresholds.collapsing_sci,
                mute_min_avg_length=config.state_thresholds.mute_min_avg_length,
                mute_min_rr=config.state_thresholds.mute_min_rr,
            ),
            rules=EvolutionRules(
                target_rr=config.evolution_rules.target_rr,
                target_rr_high=config.evolution_rules.target_rr_high,
                target_rd=config.evolution_rules.target_rd,
                target_rld=config.evolution_rules.target_rld,
                target_rf=config.evolution_rules.target_rf,
                target_rf_low=config.evolution_rules.target_rf_low,
                target_sci=config.evolution_rules.target_sci,
                length_relax_weight=config.evolution_rules.length_relax_weight,
                length_tighten_weight=config.evolution_rules.length_tighten_weight,
                refusal_raise_weight=config.evolution_rules.refusal_raise_weight,
                refusal_lower_weight=config.evolution_rules.refusal_lower_weight,
                perturbation_weight=config.evolution_rules.perturbation_weight,
                temperature_weight=config.evolution_rules.temperature_weight,
                length_scale=config.evolution_rules.length_scale,
                refusal_scale=config.evolution_rules.refusal_scale,
                perturbation_scale=config.evolution_rules.perturbation_scale,
                temperature_scale=config.evolution_rules.temperature_scale,
                action_threshold_tokens=config.evolution_rules.action_threshold_tokens,
                action_threshold_ratio=config.evolution_rules.action_threshold_ratio,
                min_output_tokens=config.evolution_rules.min_output_tokens,
                max_output_tokens=config.evolution_rules.max_output_tokens,
                min_temperature=config.evolution_rules.min_temperature,
                max_temperature=config.evolution_rules.max_temperature,
            ),
        )
    
    def compute_iteration_metrics(
        self,
        current_interactions: Sequence[Interaction],
        previous_interactions: Sequence[Interaction] | None = None,
    ) -> tuple[IterationMetrics, SystemState]:
        """
        Compute metrics and evaluate state.
        
        Core computational method of the Trainer (修炼者).
        通过计算观照自身状态。
        """
        metrics = compute_metrics(current_interactions, previous_interactions)
        previous_metrics = (
            compute_metrics(previous_interactions) if previous_interactions else None
        )
        state = evaluate_state(metrics, previous_metrics, self.thresholds)
        return metrics, state
    
    def evolve_policy(
        self,
        metrics: IterationMetrics,
        previous_metrics: IterationMetrics | None,
        current_policy: PromptPolicy,
    ) -> tuple[list[EvolutionAction], PromptPolicy, str]:
        """
        Evolve prompt policy based on metrics.
        
        Core evolution method of the Trainer (修炼者).
        通过演化调整策略。
        """
        return evolve_prompt(metrics, previous_metrics, current_policy, self.rules)
    
    def run_iteration_cycle(
        self,
        iteration_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> TrainerIterationResult:
        """
        Execute complete iteration cycle.
        
        This is the main method called by the Scheduler.
        修炼者的主要迭代方法，由调度器调用。
        
        Steps:
        1. Load interactions from archive
        2. Compute metrics
        3. Evaluate state
        4. Evolve policy (if not frozen)
        5. Save results to archive
        
        Returns iteration result for Scheduler to coordinate.
        """
        print(f"\n[Trainer] Running iteration cycle {iteration_id}")
        
        # Load current interactions
        current_interactions = self.archive.load_interactions_by_time_window(
            start_time=start_time,
            end_time=end_time,
        )
        
        if not current_interactions:
            raise ValueError("No interactions found in time window")
        
        print(f"[Trainer] Loaded {len(current_interactions)} current interactions")
        
        # Get previous iteration
        latest_iteration = self.archive.get_latest_iteration()
        previous_interactions = []
        if latest_iteration:
            previous_interactions = self.archive.load_interactions_by_iteration(
                latest_iteration.id
            )
            print(f"[Trainer] Loaded {len(previous_interactions)} previous interactions")
        
        # Compute metrics and evaluate state
        metrics, state = self.compute_iteration_metrics(
            current_interactions,
            previous_interactions,
        )
        
        print(f"[Trainer] Metrics computed:")
        print(f"  Resonance Ratio: {metrics.resonance_ratio:.3f}")
        print(f"  Rejection Density: {metrics.rejection_density:.3f}")
        print(f"  Response Length Drift: {metrics.response_length_drift:.3f}")
        print(f"  Refusal Frequency: {metrics.refusal_frequency:.3f}")
        print(f"  Semantic Collapse Index: {metrics.semantic_collapse_index:.3f}")
        print(f"[Trainer] State evaluated: {state.value}")
        
        # Save metrics snapshot
        self.archive.save_metrics_snapshot(iteration_id, metrics)
        
        # Evolve policy (if not frozen)
        new_prompt_version = None
        evolution_actions = []
        
        if self.archive.is_frozen():
            print("[Trainer] System is FROZEN. Skipping policy evolution.")
        else:
            current_prompt = self.archive.get_latest_prompt()
            if not current_prompt:
                raise RuntimeError("No current prompt found in archive")
            
            current_policy = PromptPolicy.from_dict(current_prompt.policy)
            previous_metrics = compute_metrics(previous_interactions) if previous_interactions else None
            
            # Evolve policy
            actions, next_policy, next_prompt = self.evolve_policy(
                metrics,
                previous_metrics,
                current_policy,
            )
            
            print(f"[Trainer] Evolution actions: {[a.value for a in actions]}")
            print(f"[Trainer] Next policy: max_tokens={next_policy.max_output_tokens}, "
                  f"refusal={next_policy.refusal_threshold:.2f}, "
                  f"temp={next_policy.temperature:.2f}")
            
            # Save new prompt
            new_version = current_prompt.version + 1
            self.archive.save_prompt(
                version=new_version,
                prompt_text=next_prompt,
                policy=next_policy.to_dict(),
                actions=[a.value for a in actions],
            )
            
            new_prompt_version = new_version
            evolution_actions = actions
            print(f"[Trainer] New prompt version {new_version} saved.")
        
        return TrainerIterationResult(
            iteration_id=iteration_id,
            state=state,
            metrics=metrics,
            evolution_actions=evolution_actions,
            new_prompt_version=new_prompt_version,
        )
