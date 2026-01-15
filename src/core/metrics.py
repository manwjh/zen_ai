from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence

from .models import Interaction, IterationMetrics


def _token_diversity(texts: Iterable[str]) -> float:
    tokens: list[str] = []
    for text in texts:
        tokens.extend(text.split())
    if not tokens:
        return 0.0
    unique = len(set(tokens))
    return unique / len(tokens)


def _sliding_rejection_density(
    interactions: Sequence[Interaction],
    window_size: int,
) -> float:
    if not interactions:
        return 0.0
    size = max(1, min(window_size, len(interactions)))
    max_density = 0.0
    for start in range(0, len(interactions) - size + 1):
        window = interactions[start : start + size]
        rejections = sum(
            1 for item in window if item.feedback == "rejection"
        )
        max_density = max(max_density, rejections / size)
    return max_density


def compute_metrics(
    interactions: Sequence[Interaction],
    previous_interactions: Sequence[Interaction] | None = None,
    window_size: int = 5,
) -> IterationMetrics:
    if not interactions:
        return IterationMetrics(
            total_responses=0,
            resonance_ratio=0.0,
            rejection_density=0.0,
            response_length_drift=1.0,
            refusal_frequency=0.0,
            semantic_collapse_index=0.0,
            average_response_length=0.0,
        )

    total = len(interactions)
    resonance = sum(
        1 for item in interactions if item.feedback == "resonance"
    )
    refusals = sum(1 for item in interactions if item.refusal)
    rejection_density = _sliding_rejection_density(interactions, window_size)
    average_length = sum(item.response_length for item in interactions) / total

    if previous_interactions:
        prev_avg_length = sum(
            item.response_length for item in previous_interactions
        ) / max(1, len(previous_interactions))
        response_length_drift = average_length / prev_avg_length if prev_avg_length else 1.0
    else:
        response_length_drift = 1.0

    if previous_interactions:
        prev_diversity = _token_diversity(
            item.response_text for item in previous_interactions
        )
    else:
        prev_diversity = _token_diversity(item.response_text for item in interactions)
    current_diversity = _token_diversity(item.response_text for item in interactions)
    if prev_diversity > 0:
        semantic_collapse_index = max(
            0.0, min(1.0, (prev_diversity - current_diversity) / prev_diversity)
        )
    else:
        semantic_collapse_index = 0.0

    return IterationMetrics(
        total_responses=total,
        resonance_ratio=resonance / total,
        rejection_density=rejection_density,
        response_length_drift=response_length_drift,
        refusal_frequency=refusals / total,
        semantic_collapse_index=semantic_collapse_index,
        average_response_length=average_length,
    )
