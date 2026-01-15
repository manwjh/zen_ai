from __future__ import annotations

from dataclasses import dataclass

from .models import IterationMetrics, SystemState


@dataclass(frozen=True)
class StateThresholds:
    """
    State evaluation thresholds.
    
    DEPRECATED: Use StateThresholdsConfig from src.config instead.
    This class is kept for backward compatibility.
    """
    stable_min_rr: float
    stable_max_rd: float
    stable_min_rld: float
    stable_max_rf: float
    stable_max_sci: float
    drifting_rr_drop: float
    collapsing_rr: float
    collapsing_rd: float
    collapsing_sci: float
    mute_min_avg_length: float
    mute_min_rr: float
    
    @classmethod
    def from_config(cls, config) -> StateThresholds:
        """Create StateThresholds from StateThresholdsConfig"""
        return cls(
            stable_min_rr=config.stable_min_rr,
            stable_max_rd=config.stable_max_rd,
            stable_min_rld=config.stable_min_rld,
            stable_max_rf=config.stable_max_rf,
            stable_max_sci=config.stable_max_sci,
            drifting_rr_drop=config.drifting_rr_drop,
            collapsing_rr=config.collapsing_rr,
            collapsing_rd=config.collapsing_rd,
            collapsing_sci=config.collapsing_sci,
            mute_min_avg_length=config.mute_min_avg_length,
            mute_min_rr=config.mute_min_rr,
        )


def evaluate_state(
    metrics: IterationMetrics,
    previous_metrics: IterationMetrics | None = None,
    thresholds: StateThresholds | None = None,
) -> SystemState:
    if thresholds is None:
        raise ValueError(
            "StateThresholds is required. "
            "All configuration must be explicitly provided."
        )

    if metrics.total_responses == 0:
        return SystemState.MUTE

    if (
        metrics.average_response_length <= thresholds.mute_min_avg_length
        or metrics.resonance_ratio <= thresholds.mute_min_rr
    ):
        return SystemState.MUTE

    if (
        metrics.resonance_ratio <= thresholds.collapsing_rr
        and metrics.rejection_density >= thresholds.collapsing_rd
    ) or metrics.semantic_collapse_index >= thresholds.collapsing_sci:
        return SystemState.COLLAPSING

    if previous_metrics and (
        previous_metrics.resonance_ratio - metrics.resonance_ratio
        >= thresholds.drifting_rr_drop
    ):
        return SystemState.DRIFTING

    if (
        metrics.resonance_ratio >= thresholds.stable_min_rr
        and metrics.rejection_density <= thresholds.stable_max_rd
        and metrics.response_length_drift >= thresholds.stable_min_rld
        and metrics.refusal_frequency <= thresholds.stable_max_rf
        and metrics.semantic_collapse_index <= thresholds.stable_max_sci
    ):
        return SystemState.STABLE

    return SystemState.DRIFTING
