#!/usr/bin/env python3
"""
Test strict configuration loading behavior.

Ensures that all configuration parameters must be explicitly defined
and missing parameters cause immediate failure.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import load_config


def test_missing_config_file():
    """Test that missing config file raises FileNotFoundError"""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config("nonexistent.yml")


def test_empty_config_file():
    """Test that empty config file raises ValueError"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("")
        config_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Configuration file is empty"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()


def test_missing_required_section():
    """Test that missing required section raises KeyError"""
    config_data = {
        "paths": {
            "data_dir": "data",
            "database": "data/zenai.db",
            "reports_dir": "reports",
        },
        # Missing scheduler, initial_policy, etc.
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        with pytest.raises(KeyError, match="Missing required configuration sections"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()


def test_missing_required_parameter():
    """Test that missing required parameter raises TypeError"""
    config_data = {
        "paths": {
            "data_dir": "data",
            # Missing database and reports_dir
        },
        "scheduler": {
            "time_window_hours": 24,
            "min_interactions": 100,
            "check_interval_minutes": 60,
        },
        "initial_policy": {
            "max_output_tokens": 220,
            "refusal_threshold": 0.25,
            "perturbation_level": 0.1,
            "temperature": 0.7,
        },
        "state_thresholds": {
            "stable_min_rr": 0.25,
            "stable_max_rd": 0.4,
            "stable_min_rld": 0.8,
            "stable_max_rf": 0.35,
            "stable_max_sci": 0.3,
            "drifting_rr_drop": 0.1,
            "collapsing_rr": 0.15,
            "collapsing_rd": 0.7,
            "collapsing_sci": 0.6,
            "mute_min_avg_length": 8.0,
            "mute_min_rr": 0.05,
        },
        "evolution_rules": {
            "target_rr": 0.4,
            "target_rr_high": 0.55,
            "target_rd": 0.3,
            "target_rld": 0.9,
            "target_rf": 0.2,
            "target_rf_low": 0.08,
            "target_sci": 0.2,
            "length_relax_weight": 1.0,
            "length_tighten_weight": 1.2,
            "refusal_raise_weight": 1.0,
            "refusal_lower_weight": 0.8,
            "perturbation_weight": 1.0,
            "temperature_weight": 0.6,
            "length_scale": 80.0,
            "refusal_scale": 0.25,
            "perturbation_scale": 0.2,
            "temperature_scale": 0.3,
            "action_threshold_tokens": 5,
            "action_threshold_ratio": 0.01,
            "min_output_tokens": 80,
            "max_output_tokens": 420,
            "min_temperature": 0.2,
            "max_temperature": 1.2,
        },
        "safety_thresholds": {
            "kill_consecutive_collapsing": 3,
            "kill_consecutive_mute": 5,
            "kill_min_rr": 0.05,
            "kill_max_rd": 0.9,
            "kill_max_sci": 0.8,
        },
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        with pytest.raises(TypeError, match="Missing required parameters in 'paths'"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()


def test_valid_config_loads_successfully():
    """Test that valid config loads without errors"""
    config_data = {
        "paths": {
            "data_dir": "data",
            "database": "data/zenai.db",
            "reports_dir": "reports",
        },
        "scheduler": {
            "time_window_hours": 24,
            "min_interactions": 100,
            "check_interval_minutes": 60,
        },
        "initial_policy": {
            "max_output_tokens": 220,
            "refusal_threshold": 0.25,
            "perturbation_level": 0.1,
            "temperature": 0.7,
        },
        "state_thresholds": {
            "stable_min_rr": 0.25,
            "stable_max_rd": 0.4,
            "stable_min_rld": 0.8,
            "stable_max_rf": 0.35,
            "stable_max_sci": 0.3,
            "drifting_rr_drop": 0.1,
            "collapsing_rr": 0.15,
            "collapsing_rd": 0.7,
            "collapsing_sci": 0.6,
            "mute_min_avg_length": 8.0,
            "mute_min_rr": 0.05,
        },
        "evolution_rules": {
            "target_rr": 0.4,
            "target_rr_high": 0.55,
            "target_rd": 0.3,
            "target_rld": 0.9,
            "target_rf": 0.2,
            "target_rf_low": 0.08,
            "target_sci": 0.2,
            "length_relax_weight": 1.0,
            "length_tighten_weight": 1.2,
            "refusal_raise_weight": 1.0,
            "refusal_lower_weight": 0.8,
            "perturbation_weight": 1.0,
            "temperature_weight": 0.6,
            "length_scale": 80.0,
            "refusal_scale": 0.25,
            "perturbation_scale": 0.2,
            "temperature_scale": 0.3,
            "action_threshold_tokens": 5,
            "action_threshold_ratio": 0.01,
            "min_output_tokens": 80,
            "max_output_tokens": 420,
            "min_temperature": 0.2,
            "max_temperature": 1.2,
        },
        "safety_thresholds": {
            "kill_consecutive_collapsing": 3,
            "kill_consecutive_mute": 5,
            "kill_min_rr": 0.05,
            "kill_max_rd": 0.9,
            "kill_max_sci": 0.8,
        },
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        config = load_config(config_path)
        
        # Verify config loaded correctly
        assert config.paths.data_dir == "data"
        assert config.paths.database == "data/zenai.db"
        assert config.scheduler.time_window_hours == 24
        assert config.initial_policy.max_output_tokens == 220
        assert config.state_thresholds.stable_min_rr == 0.25
        assert config.evolution_rules.target_rr == 0.4
        assert config.safety_thresholds.kill_consecutive_collapsing == 3
    finally:
        Path(config_path).unlink()


def test_no_default_values_in_dataclasses():
    """Test that config dataclasses don't have default values"""
    from src.config.models import (
        EvolutionRulesConfig,
        InitialPolicyConfig,
        PathConfig,
        SafetyThresholdsConfig,
        SchedulerConfig,
        StateThresholdsConfig,
    )
    
    # Try to create instances without parameters - should fail
    with pytest.raises(TypeError):
        PathConfig()  # type: ignore
    
    with pytest.raises(TypeError):
        SchedulerConfig()  # type: ignore
    
    with pytest.raises(TypeError):
        InitialPolicyConfig()  # type: ignore
    
    with pytest.raises(TypeError):
        StateThresholdsConfig()  # type: ignore
    
    with pytest.raises(TypeError):
        EvolutionRulesConfig()  # type: ignore
    
    with pytest.raises(TypeError):
        SafetyThresholdsConfig()  # type: ignore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
