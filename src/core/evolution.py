from __future__ import annotations

from dataclasses import dataclass

from .models import EvolutionAction, IterationMetrics, PromptPolicy
from .prompt import render_prompt


@dataclass(frozen=True)
class EvolutionRules:
    """
    Evolution rules for prompt adaptation.
    
    DEPRECATED: Use EvolutionRulesConfig from src.config instead.
    This class is kept for backward compatibility.
    """
    target_rr: float
    target_rr_high: float
    target_rd: float
    target_rld: float
    target_rf: float
    target_rf_low: float
    target_sci: float
    length_relax_weight: float
    length_tighten_weight: float
    refusal_raise_weight: float
    refusal_lower_weight: float
    perturbation_weight: float
    temperature_weight: float
    length_scale: float
    refusal_scale: float
    perturbation_scale: float
    temperature_scale: float
    action_threshold_tokens: int
    action_threshold_ratio: float
    min_output_tokens: int
    max_output_tokens: int
    min_temperature: float
    max_temperature: float
    
    @classmethod
    def from_config(cls, config) -> EvolutionRules:
        """Create EvolutionRules from EvolutionRulesConfig"""
        return cls(
            target_rr=config.target_rr,
            target_rr_high=config.target_rr_high,
            target_rd=config.target_rd,
            target_rld=config.target_rld,
            target_rf=config.target_rf,
            target_rf_low=config.target_rf_low,
            target_sci=config.target_sci,
            length_relax_weight=config.length_relax_weight,
            length_tighten_weight=config.length_tighten_weight,
            refusal_raise_weight=config.refusal_raise_weight,
            refusal_lower_weight=config.refusal_lower_weight,
            perturbation_weight=config.perturbation_weight,
            temperature_weight=config.temperature_weight,
            length_scale=config.length_scale,
            refusal_scale=config.refusal_scale,
            perturbation_scale=config.perturbation_scale,
            temperature_scale=config.temperature_scale,
            action_threshold_tokens=config.action_threshold_tokens,
            action_threshold_ratio=config.action_threshold_ratio,
            min_output_tokens=config.min_output_tokens,
            max_output_tokens=config.max_output_tokens,
            min_temperature=config.min_temperature,
            max_temperature=config.max_temperature,
        )


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def evolve_policy(
    metrics: IterationMetrics,
    previous_metrics: IterationMetrics | None,
    policy: PromptPolicy,
    rules: EvolutionRules | None = None,
) -> tuple[list[EvolutionAction], PromptPolicy]:
    if rules is None:
        raise ValueError(
            "EvolutionRules is required. "
            "All configuration must be explicitly provided."
        )
    actions: list[EvolutionAction] = []
    del previous_metrics

    rr_low = max(0.0, rules.target_rr - metrics.resonance_ratio)
    rr_high = max(0.0, metrics.resonance_ratio - rules.target_rr_high)
    rd_high = max(0.0, metrics.rejection_density - rules.target_rd)
    rld_drop = max(0.0, rules.target_rld - metrics.response_length_drift)
    rf_high = max(0.0, metrics.refusal_frequency - rules.target_rf)
    rf_low = max(0.0, rules.target_rf_low - metrics.refusal_frequency)
    sci_high = max(0.0, metrics.semantic_collapse_index - rules.target_sci)

    length_delta = (
        rules.length_relax_weight * (rld_drop + rf_high)
        - rules.length_tighten_weight * (rr_low + rd_high)
    )
    token_delta = int(round(length_delta * rules.length_scale))

    refusal_delta = (
        rules.refusal_raise_weight * (rr_low + rd_high + rr_high + rf_low)
        - rules.refusal_lower_weight * (rf_high + rld_drop)
    )
    refusal_shift = refusal_delta * rules.refusal_scale

    perturbation_shift = sci_high * rules.perturbation_weight * rules.perturbation_scale

    temperature_delta = rules.temperature_weight * (sci_high - rr_low - rd_high)
    temperature_shift = temperature_delta * rules.temperature_scale

    if token_delta <= -rules.action_threshold_tokens:
        actions.append(EvolutionAction.TIGHTEN_LENGTH)
    elif token_delta >= rules.action_threshold_tokens:
        actions.append(EvolutionAction.RELAX_LENGTH)

    if refusal_shift >= rules.action_threshold_ratio:
        actions.append(EvolutionAction.RAISE_REFUSAL_THRESHOLD)
    elif refusal_shift <= -rules.action_threshold_ratio:
        actions.append(EvolutionAction.LOWER_REFUSAL_THRESHOLD)

    if perturbation_shift >= rules.action_threshold_ratio:
        actions.append(EvolutionAction.MILD_PERTURBATION)

    if abs(temperature_shift) >= rules.action_threshold_ratio:
        actions.append(EvolutionAction.TUNE_TEMPERATURE)

    next_policy = PromptPolicy(
        max_output_tokens=int(
            _clamp(
                policy.max_output_tokens + token_delta,
                rules.min_output_tokens,
                rules.max_output_tokens,
            )
        ),
        refusal_threshold=_clamp(
            policy.refusal_threshold + refusal_shift,
            0.0,
            1.0,
        ),
        perturbation_level=_clamp(
            policy.perturbation_level + perturbation_shift,
            0.0,
            1.0,
        ),
        temperature=_clamp(
            policy.temperature + temperature_shift,
            rules.min_temperature,
            rules.max_temperature,
        ),
    )

    return actions, next_policy


def evolve_prompt(
    metrics: IterationMetrics,
    previous_metrics: IterationMetrics | None,
    policy: PromptPolicy,
    rules: EvolutionRules | None = None,
) -> tuple[list[EvolutionAction], PromptPolicy, str]:
    actions, next_policy = evolve_policy(metrics, previous_metrics, policy, rules)
    return actions, next_policy, render_prompt(next_policy)
