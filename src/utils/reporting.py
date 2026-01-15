from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..trainer import TrainerIterationResult


@dataclass(frozen=True)
class IterationReport:
    """
    Iteration report for analysis and debugging.
    
    This is a simplified representation of iteration results
    for external consumption (JSON export, analysis, etc.)
    """
    iteration_id: int
    metrics: dict[str, float | int]
    state: str
    actions: list[str]
    prompt_version: int | None


def build_report(
    result: TrainerIterationResult,
) -> IterationReport:
    """
    Build iteration report from Trainer result.
    
    Simplified - no longer needs separate policy objects.
    """
    return IterationReport(
        iteration_id=result.iteration_id,
        metrics=result.metrics.to_dict(),
        state=result.state.value,
        actions=[action.value for action in result.evolution_actions],
        prompt_version=result.new_prompt_version,
    )


def save_report(report: IterationReport, path: str | Path) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(_report_to_payload(report), indent=2),
        encoding="utf-8",
    )


def load_report(path: str | Path) -> IterationReport:
    report_path = Path(path)
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    return _parse_report(payload, report_path)


def _parse_report(payload: dict[str, Any], report_path: Path) -> IterationReport:
    required_keys = [
        "iteration_id",
        "metrics",
        "state",
        "actions",
        "prompt_version",
    ]
    missing = [key for key in required_keys if key not in payload]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"Missing keys in report {report_path}: {missing_list}")

    return IterationReport(
        iteration_id=int(payload["iteration_id"]),
        metrics=payload["metrics"],
        state=str(payload["state"]),
        actions=list(payload["actions"]),
        prompt_version=payload["prompt_version"],
    )


def _report_to_payload(report: IterationReport) -> dict[str, Any]:
    return {
        "iteration_id": report.iteration_id,
        "metrics": report.metrics,
        "state": report.state,
        "actions": report.actions,
        "prompt_version": report.prompt_version,
    }


def summarize_report(report: IterationReport) -> dict[str, float | int | str]:
    metrics = report.metrics
    return {
        "state": report.state,
        "total_responses": int(metrics.get("total_responses", 0)),
        "resonance_ratio": float(metrics.get("resonance_ratio", 0.0)),
        "rejection_density": float(metrics.get("rejection_density", 0.0)),
        "refusal_frequency": float(metrics.get("refusal_frequency", 0.0)),
        "semantic_collapse_index": float(metrics.get("semantic_collapse_index", 0.0)),
        "actions_count": len(report.actions),
        "prompt_version": report.prompt_version,
    }


def compare_reports(
    earlier: IterationReport,
    later: IterationReport,
) -> dict[str, float]:
    metrics_keys = [
        "resonance_ratio",
        "rejection_density",
        "response_length_drift",
        "refusal_frequency",
        "semantic_collapse_index",
        "average_response_length",
    ]
    deltas: dict[str, float] = {}
    for key in metrics_keys:
        before = float(earlier.metrics.get(key, 0.0))
        after = float(later.metrics.get(key, 0.0))
        deltas[f"{key}_delta"] = after - before
    return deltas
