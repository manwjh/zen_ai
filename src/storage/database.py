from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class InteractionRecord(Base):
    """Single user-system interaction with feedback"""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    iteration_id = Column(Integer, nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_input = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    feedback = Column(String(500), nullable=False)  # Free-form text feedback (up to 500 chars)
    refusal = Column(Boolean, nullable=False, default=False)
    extra_data = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)

    def __repr__(self) -> str:
        return (
            f"<InteractionRecord(id={self.id}, "
            f"iteration_id={self.iteration_id}, "
            f"feedback={self.feedback})>"
        )


class IterationSession(Base):
    """Iteration session metadata and results"""
    __tablename__ = "iterations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    total_interactions = Column(Integer, nullable=False, default=0)
    state = Column(String(20), nullable=False)  # stable/drifting/collapsing/mute/dead
    metrics = Column(JSON, nullable=False)  # All computed metrics
    prompt_version = Column(Integer, nullable=False)
    gatha_metadata = Column(JSON, nullable=True)  # All gatha-related data (gatha, explanation, audio, etc.)

    def __repr__(self) -> str:
        return (
            f"<IterationSession(id={self.id}, "
            f"state={self.state}, "
            f"prompt_version={self.prompt_version})>"
        )


class MetricsSnapshot(Base):
    """Point-in-time metrics snapshot"""
    __tablename__ = "metrics_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    iteration_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    resonance_ratio = Column(Float, nullable=False)
    rejection_density = Column(Float, nullable=False)
    response_length_drift = Column(Float, nullable=False)
    refusal_frequency = Column(Float, nullable=False)
    semantic_collapse_index = Column(Float, nullable=False)
    average_response_length = Column(Float, nullable=False)
    total_responses = Column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<MetricsSnapshot(id={self.id}, "
            f"iteration_id={self.iteration_id}, "
            f"rr={self.resonance_ratio:.3f})>"
        )


class PromptHistory(Base):
    """Prompt version history with policies"""
    __tablename__ = "prompt_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    prompt_text = Column(Text, nullable=False)
    policy = Column(JSON, nullable=False)  # max_output_tokens, refusal_threshold, etc.
    actions = Column(JSON, nullable=True)  # Evolution actions that led to this prompt
    
    def __repr__(self) -> str:
        return f"<PromptHistory(version={self.version}, timestamp={self.timestamp})>"


class SystemStatus(Base):
    """Global system status and control flags"""
    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), nullable=False, unique=True, index=True)
    value = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<SystemStatus(key={self.key}, value={self.value})>"


def create_database(db_path: str | Path) -> Any:
    """Create database engine and initialize tables"""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(f"sqlite:///{db_file}", echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session_maker(engine: Any) -> Any:
    """Create session maker from engine"""
    return sessionmaker(bind=engine)
