from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence


class SystemState(str, Enum):
    STABLE = "stable"
    DRIFTING = "drifting"
    COLLAPSING = "collapsing"
    MUTE = "mute"
    DEAD = "dead"


class EvolutionAction(str, Enum):
    TIGHTEN_LENGTH = "tighten_length"
    RELAX_LENGTH = "relax_length"
    RAISE_REFUSAL_THRESHOLD = "raise_refusal_threshold"
    LOWER_REFUSAL_THRESHOLD = "lower_refusal_threshold"
    MILD_PERTURBATION = "mild_perturbation"
    TUNE_TEMPERATURE = "tune_temperature"


@dataclass(frozen=True)
class Interaction:
    user_input: str
    response_text: str
    feedback: str  # Free-form text feedback (e.g., "resonance", "rejection", "ignore", or custom text)
    refusal: bool

    @property
    def response_length(self) -> int:
        return len(self.response_text.split())


@dataclass(frozen=True)
class IterationMetrics:
    total_responses: int
    resonance_ratio: float
    rejection_density: float
    response_length_drift: float
    refusal_frequency: float
    semantic_collapse_index: float
    average_response_length: float
    
    def to_dict(self) -> dict[str, float | int]:
        """Convert metrics to dictionary for storage"""
        return {
            "total_responses": self.total_responses,
            "resonance_ratio": self.resonance_ratio,
            "rejection_density": self.rejection_density,
            "response_length_drift": self.response_length_drift,
            "refusal_frequency": self.refusal_frequency,
            "semantic_collapse_index": self.semantic_collapse_index,
            "average_response_length": self.average_response_length,
        }


@dataclass(frozen=True)
class PromptPolicy:
    max_output_tokens: int
    refusal_threshold: float
    perturbation_level: float
    temperature: float
    
    def to_dict(self) -> dict[str, float | int]:
        """Convert policy to dictionary for storage"""
        return {
            "max_output_tokens": self.max_output_tokens,
            "refusal_threshold": self.refusal_threshold,
            "perturbation_level": self.perturbation_level,
            "temperature": self.temperature,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, float | int]) -> PromptPolicy:
        """Create policy from dictionary"""
        return cls(
            max_output_tokens=int(data["max_output_tokens"]),
            refusal_threshold=float(data["refusal_threshold"]),
            perturbation_level=float(data["perturbation_level"]),
            temperature=float(data["temperature"]),
        )


@dataclass(frozen=True)
class PromptSnapshot:
    version: int
    policy: PromptPolicy
    prompt_text: str


@dataclass(frozen=True)
class EvolutionDecision:
    actions: Sequence[EvolutionAction]
    next_policy: PromptPolicy
    next_prompt: str


def as_interactions(items: Iterable[Interaction]) -> Sequence[Interaction]:
    return list(items)
