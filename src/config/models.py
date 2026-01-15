"""
Configuration data models for ZenAi system.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathConfig:
    """Path configuration"""
    data_dir: str
    database: str
    reports_dir: str
    
    def get_database_path(self) -> Path:
        """Get database path as Path object"""
        return Path(self.database)
    
    def get_data_dir_path(self) -> Path:
        """Get data directory as Path object"""
        return Path(self.data_dir)
    
    def get_reports_dir_path(self) -> Path:
        """Get reports directory as Path object"""
        return Path(self.reports_dir)


@dataclass(frozen=True)
class SchedulerConfig:
    """Scheduler configuration"""
    time_window_hours: int
    min_interactions: int
    check_interval_minutes: int


@dataclass(frozen=True)
class InitialPolicyConfig:
    """Initial prompt policy configuration"""
    max_output_tokens: int
    refusal_threshold: float
    perturbation_level: float
    temperature: float


@dataclass(frozen=True)
class StateThresholdsConfig:
    """State evaluation thresholds configuration"""
    # Stable state conditions
    stable_min_rr: float
    stable_max_rd: float
    stable_min_rld: float
    stable_max_rf: float
    stable_max_sci: float
    
    # Drifting detection
    drifting_rr_drop: float
    
    # Collapsing state conditions
    collapsing_rr: float
    collapsing_rd: float
    collapsing_sci: float
    
    # Mute state conditions
    mute_min_avg_length: float
    mute_min_rr: float


@dataclass(frozen=True)
class EvolutionRulesConfig:
    """Evolution rules configuration"""
    # Target metrics
    target_rr: float
    target_rr_high: float
    target_rd: float
    target_rld: float
    target_rf: float
    target_rf_low: float
    target_sci: float
    
    # Adjustment weights
    length_relax_weight: float
    length_tighten_weight: float
    refusal_raise_weight: float
    refusal_lower_weight: float
    perturbation_weight: float
    temperature_weight: float
    
    # Adjustment scales
    length_scale: float
    refusal_scale: float
    perturbation_scale: float
    temperature_scale: float
    
    # Action trigger thresholds
    action_threshold_tokens: int
    action_threshold_ratio: float
    
    # Parameter limits
    min_output_tokens: int
    max_output_tokens: int
    min_temperature: float
    max_temperature: float


@dataclass(frozen=True)
class SafetyThresholdsConfig:
    """Safety thresholds configuration"""
    kill_consecutive_collapsing: int
    kill_consecutive_mute: int
    kill_min_rr: float
    kill_max_rd: float
    kill_max_sci: float


@dataclass(frozen=True)
class ZenAiConfig:
    """Complete ZenAi system configuration"""
    paths: PathConfig
    scheduler: SchedulerConfig
    initial_policy: InitialPolicyConfig
    state_thresholds: StateThresholdsConfig
    evolution_rules: EvolutionRulesConfig
    safety_thresholds: SafetyThresholdsConfig
    
