from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ..core.models import SystemState
from ..storage import ResonanceArchive


@dataclass
class SystemMetricsSummary:
    """Real-time system metrics summary"""
    timestamp: datetime
    current_iteration_id: int | None
    prompt_version: int
    total_interactions: int
    total_iterations: int
    last_24h_interactions: int
    current_state: str
    is_frozen: bool
    is_killed: bool
    latest_metrics: dict[str, float | int] | None


@dataclass
class HealthStatus:
    """System health indicators"""
    status: str  # healthy, degraded, critical, dead
    issues: list[str]
    recommendations: list[str]


class SystemMonitor:
    """
    Real-time monitoring and health checks for ZenAi system.
    
    Provides:
    - Real-time metrics aggregation
    - Health status evaluation
    - Anomaly detection
    - Performance tracking
    """

    def __init__(self, archive: ResonanceArchive):
        self.archive = archive

    def get_current_metrics(self) -> SystemMetricsSummary:
        """Get current system metrics summary"""
        latest_iteration = self.archive.get_latest_iteration()
        latest_prompt = self.archive.get_latest_prompt()
        
        # Get interaction counts
        total_interactions = self.archive.get_interaction_count()
        last_24h = datetime.utcnow() - timedelta(hours=24)
        last_24h_interactions = self.archive.get_interaction_count(
            start_time=last_24h
        )
        
        # Get status flags
        is_frozen = self.archive.is_frozen()
        is_killed = self.archive.is_killed()
        
        return SystemMetricsSummary(
            timestamp=datetime.utcnow(),
            current_iteration_id=latest_iteration.id if latest_iteration else None,
            prompt_version=latest_prompt.version if latest_prompt else 0,
            total_interactions=total_interactions,
            total_iterations=self.archive.get_iteration_count(),
            last_24h_interactions=last_24h_interactions,
            current_state=latest_iteration.state if latest_iteration else "unknown",
            is_frozen=is_frozen,
            is_killed=is_killed,
            latest_metrics=latest_iteration.metrics if latest_iteration else None,
        )

    def check_health(self) -> HealthStatus:
        """
        Evaluate system health status.
        
        Health levels:
        - healthy: Normal operation
        - degraded: Some metrics out of range but system operational
        - critical: Multiple issues, may need intervention
        - dead: System terminated
        """
        issues: list[str] = []
        recommendations: list[str] = []
        
        # Check if killed
        if self.archive.is_killed():
            return HealthStatus(
                status="dead",
                issues=["System has been killed"],
                recommendations=["Review termination logs", "Restart with new instance"],
            )
        
        # Get latest iteration
        latest_iteration = self.archive.get_latest_iteration()
        if not latest_iteration:
            return HealthStatus(
                status="healthy",
                issues=[],
                recommendations=["No iterations yet - system initializing"],
            )
        
        metrics = latest_iteration.metrics
        state = latest_iteration.state
        
        # Check state
        try:
            system_state = SystemState(state)
        except ValueError:
            system_state = None
        
        if system_state == SystemState.COLLAPSING:
            issues.append("System is in COLLAPSING state")
            recommendations.append("Consider rollback or freeze")
        elif system_state == SystemState.MUTE:
            issues.append("System is in MUTE state")
            recommendations.append("Review prompt policy - may be too restrictive")
        elif system_state == SystemState.DRIFTING:
            issues.append("System is DRIFTING")
            recommendations.append("Monitor next iteration closely")
        
        # Check metrics
        if metrics:
            rr = float(metrics.get("resonance_ratio", 0.0))
            rd = float(metrics.get("rejection_density", 0.0))
            rf = float(metrics.get("refusal_frequency", 0.0))
            sci = float(metrics.get("semantic_collapse_index", 0.0))
            
            if rr < 0.15:
                issues.append(f"Very low resonance ratio: {rr:.3f}")
                recommendations.append("Investigate user feedback patterns")
            
            if rd > 0.7:
                issues.append(f"High rejection density: {rd:.3f}")
                recommendations.append("Review recent responses for quality issues")
            
            if rf > 0.5:
                issues.append(f"High refusal frequency: {rf:.3f}")
                recommendations.append("Consider lowering refusal threshold")
            
            if sci > 0.6:
                issues.append(f"High semantic collapse: {sci:.3f}")
                recommendations.append("Increase perturbation or temperature")
        
        # Check interaction volume
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_interactions = self.archive.get_interaction_count(start_time=last_24h)
        if recent_interactions < 100:
            issues.append(f"Low interaction volume: {recent_interactions} in 24h")
            recommendations.append("Increase user engagement or lower iteration threshold")
        
        # Check if frozen
        if self.archive.is_frozen():
            issues.append("System evolution is frozen")
            recommendations.append("Unfreeze to resume evolution if intentional pause is over")
        
        # Determine overall status
        if not issues:
            status = "healthy"
        elif len(issues) <= 2:
            status = "degraded"
        else:
            status = "critical"
        
        return HealthStatus(
            status=status,
            issues=issues,
            recommendations=recommendations,
        )

    def get_iteration_history(
        self,
        n: int = 10,
    ) -> list[dict[str, Any]]:
        """Get recent iteration history"""
        history: list[dict[str, Any]] = []
        iteration_count = self.archive.get_iteration_count()
        
        start_id = max(1, iteration_count - n + 1)
        for i in range(start_id, iteration_count + 1):
            iteration = self.archive.get_iteration(i)
            if iteration:
                history.append({
                    "id": iteration.id,
                    "start_time": iteration.start_time.isoformat(),
                    "end_time": iteration.end_time.isoformat() if iteration.end_time else None,
                    "state": iteration.state,
                    "total_interactions": iteration.total_interactions,
                    "prompt_version": iteration.prompt_version,
                    "metrics": iteration.metrics,
                })
        
        return history

    def get_prompt_evolution_history(self) -> list[dict[str, Any]]:
        """Get prompt version evolution history"""
        versions = self.archive.get_all_prompt_versions()
        history: list[dict[str, Any]] = []
        
        for version in versions:
            prompt = self.archive.load_prompt(version)
            if prompt:
                history.append({
                    "version": prompt.version,
                    "timestamp": prompt.timestamp.isoformat(),
                    "policy": prompt.policy,
                    "actions": prompt.actions,
                })
        
        return history

    def export_metrics_json(self, path: str) -> None:
        """Export current metrics to JSON file"""
        metrics = self.get_current_metrics()
        health = self.check_health()
        
        export_data = {
            "timestamp": metrics.timestamp.isoformat(),
            "system": {
                "current_iteration_id": metrics.current_iteration_id,
                "prompt_version": metrics.prompt_version,
                "state": metrics.current_state,
                "frozen": metrics.is_frozen,
                "killed": metrics.is_killed,
            },
            "interactions": {
                "total": metrics.total_interactions,
                "last_24h": metrics.last_24h_interactions,
            },
            "iterations": {
                "total": metrics.total_iterations,
            },
            "health": {
                "status": health.status,
                "issues": health.issues,
                "recommendations": health.recommendations,
            },
            "latest_metrics": metrics.latest_metrics,
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns metrics as plain text in Prometheus exposition format.
        """
        metrics = self.get_current_metrics()
        health = self.check_health()
        
        lines: list[str] = []
        
        # System info
        lines.append(f"# HELP zenai_prompt_version Current prompt version")
        lines.append(f"# TYPE zenai_prompt_version gauge")
        lines.append(f"zenai_prompt_version {metrics.prompt_version}")
        
        lines.append(f"# HELP zenai_total_interactions Total interactions")
        lines.append(f"# TYPE zenai_total_interactions counter")
        lines.append(f"zenai_total_interactions {metrics.total_interactions}")
        
        lines.append(f"# HELP zenai_last_24h_interactions Interactions in last 24 hours")
        lines.append(f"# TYPE zenai_last_24h_interactions gauge")
        lines.append(f"zenai_last_24h_interactions {metrics.last_24h_interactions}")
        
        lines.append(f"# HELP zenai_total_iterations Total iterations completed")
        lines.append(f"# TYPE zenai_total_iterations counter")
        lines.append(f"zenai_total_iterations {metrics.total_iterations}")
        
        # Status flags
        lines.append(f"# HELP zenai_frozen System frozen flag (1=frozen, 0=active)")
        lines.append(f"# TYPE zenai_frozen gauge")
        lines.append(f"zenai_frozen {1 if metrics.is_frozen else 0}")
        
        lines.append(f"# HELP zenai_killed System killed flag (1=killed, 0=alive)")
        lines.append(f"# TYPE zenai_killed gauge")
        lines.append(f"zenai_killed {1 if metrics.is_killed else 0}")
        
        # Health status
        health_value = {"healthy": 1, "degraded": 2, "critical": 3, "dead": 4}.get(
            health.status, 0
        )
        lines.append(f"# HELP zenai_health_status Health status (1=healthy, 2=degraded, 3=critical, 4=dead)")
        lines.append(f"# TYPE zenai_health_status gauge")
        lines.append(f"zenai_health_status {health_value}")
        
        # Latest metrics
        if metrics.latest_metrics:
            for key, value in metrics.latest_metrics.items():
                metric_name = f"zenai_{key}"
                lines.append(f"# HELP {metric_name} Latest {key}")
                lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f"{metric_name} {value}")
        
        return "\n".join(lines) + "\n"
