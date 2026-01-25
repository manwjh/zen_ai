from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

from sqlalchemy.orm import Session, attributes

from ..core.models import Interaction, IterationMetrics
from .database import (
    InteractionRecord,
    IterationSession,
    MetricsSnapshot,
    PromptHistory,
    SystemStatus,
    create_database,
    get_session_maker,
)


@dataclass
class ResonanceArchive:
    """
    Persistent storage for interactions and system state.
    Implements the Resonance Archive layer from design spec.
    """
    db_path: str | Path
    engine: Any = None
    session_maker: Any = None

    def __post_init__(self):
        if self.engine is None:
            self.engine = create_database(self.db_path)
            self.session_maker = get_session_maker(self.engine)

    def create_session(self) -> Session:
        """Create a new database session"""
        return self.session_maker()

    # ========================================
    # Interaction Management
    # ========================================

    def record_interaction(
        self,
        user_input: str,
        response_text: str,
        feedback: str | None = None,
        refusal: bool = False,
        iteration_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Record a single interaction to the archive.
        Returns the interaction ID.
        """
        with self.create_session() as session:
            record = InteractionRecord(
                iteration_id=iteration_id,
                user_input=user_input,
                response_text=response_text,
                feedback=feedback if feedback else "ignore",
                refusal=refusal,
                extra_data=metadata or {},  # Using extra_data column
            )
            session.add(record)
            session.commit()
            return record.id

    def update_interaction_feedback(
        self,
        interaction_id: int,
        feedback: str,
        feedback_data: dict[str, Any] | None = None,
    ) -> None:
        """
        Update feedback for an existing interaction
        
        Args:
            interaction_id: Interaction ID
            feedback: Standard feedback type (resonance/rejection/ignore)
            feedback_data: Additional feedback data (behavior, comment, etc.)
        """
        with self.create_session() as session:
            record = session.query(InteractionRecord).filter_by(id=interaction_id).first()
            if record:
                record.feedback = feedback
                # Merge feedback_data into existing extra_data
                if feedback_data:
                    existing_data = record.extra_data or {}
                    existing_data.update(feedback_data)
                    record.extra_data = existing_data
                    # Mark the JSON field as modified so SQLAlchemy tracks it
                    attributes.flag_modified(record, 'extra_data')
                session.commit()

    def load_interactions_by_iteration(
        self,
        iteration_id: int,
    ) -> Sequence[Interaction]:
        """Load all interactions for a specific iteration"""
        with self.create_session() as session:
            records = (
                session.query(InteractionRecord)
                .filter_by(iteration_id=iteration_id)
                .order_by(InteractionRecord.timestamp)
                .all()
            )
            return [self._record_to_interaction(record) for record in records]

    def load_interactions_by_time_window(
        self,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> Sequence[Interaction]:
        """Load interactions within a time window"""
        end_time = end_time or datetime.utcnow()
        with self.create_session() as session:
            records = (
                session.query(InteractionRecord)
                .filter(
                    InteractionRecord.timestamp >= start_time,
                    InteractionRecord.timestamp <= end_time,
                )
                .order_by(InteractionRecord.timestamp)
                .all()
            )
            return [self._record_to_interaction(record) for record in records]

    def assign_interactions_to_iteration(
        self,
        iteration_id: int,
        interactions: list[int],
    ) -> None:
        """
        Assign interactions to an iteration.
        
        Args:
            iteration_id: Iteration ID
            interactions: List of interaction IDs to assign
        """
        with self.create_session() as session:
            session.query(InteractionRecord).filter(
                InteractionRecord.id.in_(interactions)
            ).update(
                {InteractionRecord.iteration_id: iteration_id},
                synchronize_session=False
            )
            session.commit()
    
    def load_unassigned_interactions(self) -> Sequence[Interaction]:
        """Load interactions not yet assigned to an iteration"""
        with self.create_session() as session:
            records = (
                session.query(InteractionRecord)
                .filter_by(iteration_id=None)
                .order_by(InteractionRecord.timestamp)
                .all()
            )
            return [self._record_to_interaction(record) for record in records]

    def assign_interactions_to_iteration(
        self,
        interaction_ids: Sequence[int],
        iteration_id: int,
    ) -> None:
        """Assign interactions to an iteration"""
        with self.create_session() as session:
            session.query(InteractionRecord).filter(
                InteractionRecord.id.in_(interaction_ids)
            ).update({InteractionRecord.iteration_id: iteration_id}, synchronize_session=False)
            session.commit()

    # ========================================
    # Iteration Management
    # ========================================

    def create_iteration(
        self,
        start_time: datetime,
        prompt_version: int,
    ) -> int:
        """Create a new iteration session. Returns iteration ID."""
        with self.create_session() as session:
            iteration = IterationSession(
                start_time=start_time,
                total_interactions=0,
                state="pending",
                metrics={},
                prompt_version=prompt_version,
            )
            session.add(iteration)
            session.commit()
            return iteration.id

    def complete_iteration(
        self,
        iteration_id: int,
        end_time: datetime,
        total_interactions: int,
        state: str,
        metrics: dict[str, float | int],
    ) -> None:
        """Mark iteration as complete with final metrics"""
        with self.create_session() as session:
            iteration = session.query(IterationSession).filter_by(id=iteration_id).first()
            if iteration:
                iteration.end_time = end_time
                iteration.total_interactions = total_interactions
                iteration.state = state
                iteration.metrics = metrics
                session.commit()

    def get_latest_iteration(self) -> IterationSession | None:
        """Get the most recent iteration"""
        with self.create_session() as session:
            return (
                session.query(IterationSession)
                .order_by(IterationSession.id.desc())
                .first()
            )

    def get_iteration(self, iteration_id: int) -> IterationSession | None:
        """Get specific iteration by ID"""
        with self.create_session() as session:
            return session.query(IterationSession).filter_by(id=iteration_id).first()

    # ========================================
    # Gatha Management
    # ========================================

    def save_gatha(
        self,
        iteration_id: int,
        gatha_data: dict[str, Any],
    ) -> None:
        """
        Save complete gatha data for an iteration.
        
        All gatha-related data stored in gatha_metadata JSON field.
        所有偈子相关数据存储在 gatha_metadata JSON 字段中。
        
        Args:
            iteration_id: Iteration ID
            gatha_data: Complete gatha data dict containing:
                {
                    "gatha": str,              # The verse text
                    "explanation": str,        # Plain language explanation
                    "questions_count": int,
                    "generation_time": float,
                    "resonance_ratio": float,
                    "state": str,
                    "timestamp": str,
                    "audio_generated": bool,
                    "audio_path": str|None,
                    ...
                }
        """
        with self.create_session() as session:
            iteration = session.query(IterationSession).filter_by(id=iteration_id).first()
            if iteration:
                iteration.gatha_metadata = gatha_data
                session.commit()
    
    def get_gatha(self, iteration_id: int) -> dict[str, Any] | None:
        """
        Get complete gatha data for a specific iteration.
        
        Returns:
            Complete gatha data dict, or None if not found
        """
        with self.create_session() as session:
            iteration = session.query(IterationSession).filter_by(id=iteration_id).first()
            if iteration and iteration.gatha_metadata:
                return iteration.gatha_metadata
            return None
    
    def get_all_gathas(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent gathas with their complete data.
        
        Args:
            limit: Maximum number of gathas to return
            
        Returns:
            List of dicts containing complete gatha data
        """
        with self.create_session() as session:
            iterations = (
                session.query(IterationSession)
                .filter(IterationSession.gatha_metadata.isnot(None))
                .order_by(IterationSession.id.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "iteration_id": it.id,
                    "end_time": it.end_time.isoformat() if it.end_time else None,
                    "state": it.state,
                    "metrics": it.metrics,
                    **it.gatha_metadata,  # Unpack complete gatha data
                }
                for it in iterations
            ]

    # ========================================
    # Metrics Management
    # ========================================

    def save_metrics_snapshot(
        self,
        iteration_id: int,
        metrics: IterationMetrics,
    ) -> None:
        """Save metrics snapshot for an iteration"""
        with self.create_session() as session:
            snapshot = MetricsSnapshot(
                iteration_id=iteration_id,
                resonance_ratio=metrics.resonance_ratio,
                rejection_density=metrics.rejection_density,
                response_length_drift=metrics.response_length_drift,
                refusal_frequency=metrics.refusal_frequency,
                semantic_collapse_index=metrics.semantic_collapse_index,
                average_response_length=metrics.average_response_length,
                total_responses=metrics.total_responses,
            )
            session.add(snapshot)
            session.commit()

    def load_metrics_snapshot(
        self,
        iteration_id: int,
    ) -> MetricsSnapshot | None:
        """Load metrics snapshot for an iteration"""
        with self.create_session() as session:
            return (
                session.query(MetricsSnapshot)
                .filter_by(iteration_id=iteration_id)
                .order_by(MetricsSnapshot.timestamp.desc())
                .first()
            )

    # ========================================
    # Prompt History Management
    # ========================================

    def save_prompt(
        self,
        version: int,
        prompt_text: str,
        policy: dict[str, float | int],
        actions: list[str] | None = None,
    ) -> None:
        """Save a new prompt version"""
        with self.create_session() as session:
            prompt = PromptHistory(
                version=version,
                prompt_text=prompt_text,
                policy=policy,
                actions=actions or [],
            )
            session.add(prompt)
            session.commit()

    def load_prompt(self, version: int) -> PromptHistory | None:
        """Load specific prompt version"""
        with self.create_session() as session:
            return session.query(PromptHistory).filter_by(version=version).first()

    def get_latest_prompt(self) -> PromptHistory | None:
        """Get the latest prompt version"""
        with self.create_session() as session:
            return (
                session.query(PromptHistory)
                .order_by(PromptHistory.version.desc())
                .first()
            )

    def get_all_prompt_versions(self) -> Sequence[int]:
        """Get all available prompt versions"""
        with self.create_session() as session:
            return [
                version
                for (version,) in session.query(PromptHistory.version)
                .order_by(PromptHistory.version)
                .all()
            ]

    # ========================================
    # System Status Management
    # ========================================

    def set_status(self, key: str, value: str) -> None:
        """Set a system status flag"""
        with self.create_session() as session:
            status = session.query(SystemStatus).filter_by(key=key).first()
            if status:
                status.value = value
                status.updated_at = datetime.utcnow()
            else:
                status = SystemStatus(key=key, value=value)
                session.add(status)
            session.commit()

    def get_status(self, key: str) -> str | None:
        """Get a system status flag"""
        with self.create_session() as session:
            status = session.query(SystemStatus).filter_by(key=key).first()
            return status.value if status else None

    def is_frozen(self) -> bool:
        """Check if system evolution is frozen"""
        return self.get_status("frozen") == "true"

    def is_killed(self) -> bool:
        """Check if system has been killed"""
        return self.get_status("killed") == "true"

    # ========================================
    # Statistics and Analytics
    # ========================================

    def get_interaction_count(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """Get total interaction count within time window"""
        with self.create_session() as session:
            query = session.query(InteractionRecord)
            if start_time:
                query = query.filter(InteractionRecord.timestamp >= start_time)
            if end_time:
                query = query.filter(InteractionRecord.timestamp <= end_time)
            return query.count()

    def get_iteration_count(self) -> int:
        """Get total number of completed iterations"""
        with self.create_session() as session:
            return session.query(IterationSession).count()

    # ========================================
    # Helper Methods
    # ========================================

    def _record_to_interaction(self, record: InteractionRecord) -> Interaction:
        """Convert database record to Interaction model"""
        return Interaction(
            user_input=record.user_input,
            response_text=record.response_text,
            feedback=record.feedback,
            refusal=record.refusal,
        )
