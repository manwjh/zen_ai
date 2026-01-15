"""
Configuration loader for ZenAi system.

All configuration parameters must be explicitly defined in config.yml.
No default values or fallback mechanisms are used.
Missing parameters will cause immediate failure.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .models import (
    EvolutionRulesConfig,
    InitialPolicyConfig,
    PathConfig,
    SafetyThresholdsConfig,
    SchedulerConfig,
    StateThresholdsConfig,
    ZenAiConfig,
)


def _check_required_params(data: dict[str, Any], params: list[str], section: str) -> None:
    """
    Check that all required parameters exist in the data.
    
    Raises:
        TypeError: If any required parameter is missing
    """
    missing = [p for p in params if p not in data]
    if missing:
        raise TypeError(
            f"Missing required parameters in '{section}' section: {', '.join(missing)}. "
            f"All parameters must be explicitly defined in config.yml."
        )


def load_config(config_path: str | Path = "config.yml") -> ZenAiConfig:
    """
    Load configuration from YAML file strictly.
    
    Args:
        config_path: Path to config.yml file (relative to project root)
    
    Returns:
        ZenAiConfig object with configuration from file
        
    Raises:
        FileNotFoundError: If config file does not exist
        KeyError: If required configuration section is missing
        TypeError: If required parameter is missing within a section
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}. "
            "All configuration must be explicitly defined in config.yml."
        )
    
    with open(config_file, "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)
    
    if yaml_data is None:
        raise ValueError(
            f"Configuration file is empty: {config_file}. "
            "All configuration must be explicitly defined."
        )
    
    # Build configuration strictly - all sections must exist
    required_sections = [
        "paths", "scheduler", "initial_policy", 
        "state_thresholds", "evolution_rules", "safety_thresholds"
    ]
    missing_sections = [s for s in required_sections if s not in yaml_data]
    if missing_sections:
        raise KeyError(
            f"Missing required configuration sections: {', '.join(missing_sections)}. "
            "All sections must be defined in config.yml."
        )
    
    return ZenAiConfig(
        paths=_load_path_config(yaml_data["paths"]),
        scheduler=_load_scheduler_config(yaml_data["scheduler"]),
        initial_policy=_load_initial_policy_config(yaml_data["initial_policy"]),
        state_thresholds=_load_state_thresholds_config(yaml_data["state_thresholds"]),
        evolution_rules=_load_evolution_rules_config(yaml_data["evolution_rules"]),
        safety_thresholds=_load_safety_thresholds_config(yaml_data["safety_thresholds"]),
    )


def _load_path_config(data: dict[str, Any]) -> PathConfig:
    """Load path configuration strictly"""
    _check_required_params(data, ["data_dir", "database", "reports_dir"], "paths")
    return PathConfig(
        data_dir=data["data_dir"],
        database=data["database"],
        reports_dir=data["reports_dir"],
    )


def _load_scheduler_config(data: dict[str, Any]) -> SchedulerConfig:
    """Load scheduler configuration strictly"""
    _check_required_params(data, ["time_window_hours", "min_interactions", "check_interval_minutes"], "scheduler")
    return SchedulerConfig(
        time_window_hours=data["time_window_hours"],
        min_interactions=data["min_interactions"],
        check_interval_minutes=data["check_interval_minutes"],
    )


def _load_initial_policy_config(data: dict[str, Any]) -> InitialPolicyConfig:
    """Load initial policy configuration strictly"""
    _check_required_params(data, ["max_output_tokens", "refusal_threshold", "perturbation_level", "temperature"], "initial_policy")
    return InitialPolicyConfig(
        max_output_tokens=data["max_output_tokens"],
        refusal_threshold=data["refusal_threshold"],
        perturbation_level=data["perturbation_level"],
        temperature=data["temperature"],
    )


def _load_state_thresholds_config(data: dict[str, Any]) -> StateThresholdsConfig:
    """Load state thresholds configuration strictly"""
    required_params = [
        "stable_min_rr", "stable_max_rd", "stable_min_rld", "stable_max_rf", "stable_max_sci",
        "drifting_rr_drop", "collapsing_rr", "collapsing_rd", "collapsing_sci",
        "mute_min_avg_length", "mute_min_rr"
    ]
    _check_required_params(data, required_params, "state_thresholds")
    return StateThresholdsConfig(
        stable_min_rr=data["stable_min_rr"],
        stable_max_rd=data["stable_max_rd"],
        stable_min_rld=data["stable_min_rld"],
        stable_max_rf=data["stable_max_rf"],
        stable_max_sci=data["stable_max_sci"],
        drifting_rr_drop=data["drifting_rr_drop"],
        collapsing_rr=data["collapsing_rr"],
        collapsing_rd=data["collapsing_rd"],
        collapsing_sci=data["collapsing_sci"],
        mute_min_avg_length=data["mute_min_avg_length"],
        mute_min_rr=data["mute_min_rr"],
    )


def _load_evolution_rules_config(data: dict[str, Any]) -> EvolutionRulesConfig:
    """Load evolution rules configuration strictly"""
    required_params = [
        "target_rr", "target_rr_high", "target_rd", "target_rld", "target_rf", "target_rf_low", "target_sci",
        "length_relax_weight", "length_tighten_weight", "refusal_raise_weight", "refusal_lower_weight",
        "perturbation_weight", "temperature_weight",
        "length_scale", "refusal_scale", "perturbation_scale", "temperature_scale",
        "action_threshold_tokens", "action_threshold_ratio",
        "min_output_tokens", "max_output_tokens", "min_temperature", "max_temperature"
    ]
    _check_required_params(data, required_params, "evolution_rules")
    return EvolutionRulesConfig(
        target_rr=data["target_rr"],
        target_rr_high=data["target_rr_high"],
        target_rd=data["target_rd"],
        target_rld=data["target_rld"],
        target_rf=data["target_rf"],
        target_rf_low=data["target_rf_low"],
        target_sci=data["target_sci"],
        length_relax_weight=data["length_relax_weight"],
        length_tighten_weight=data["length_tighten_weight"],
        refusal_raise_weight=data["refusal_raise_weight"],
        refusal_lower_weight=data["refusal_lower_weight"],
        perturbation_weight=data["perturbation_weight"],
        temperature_weight=data["temperature_weight"],
        length_scale=data["length_scale"],
        refusal_scale=data["refusal_scale"],
        perturbation_scale=data["perturbation_scale"],
        temperature_scale=data["temperature_scale"],
        action_threshold_tokens=data["action_threshold_tokens"],
        action_threshold_ratio=data["action_threshold_ratio"],
        min_output_tokens=data["min_output_tokens"],
        max_output_tokens=data["max_output_tokens"],
        min_temperature=data["min_temperature"],
        max_temperature=data["max_temperature"],
    )


def _load_safety_thresholds_config(data: dict[str, Any]) -> SafetyThresholdsConfig:
    """Load safety thresholds configuration strictly"""
    required_params = [
        "kill_consecutive_collapsing", "kill_consecutive_mute",
        "kill_min_rr", "kill_max_rd", "kill_max_sci"
    ]
    _check_required_params(data, required_params, "safety_thresholds")
    return SafetyThresholdsConfig(
        kill_consecutive_collapsing=data["kill_consecutive_collapsing"],
        kill_consecutive_mute=data["kill_consecutive_mute"],
        kill_min_rr=data["kill_min_rr"],
        kill_max_rd=data["kill_max_rd"],
        kill_max_sci=data["kill_max_sci"],
    )
