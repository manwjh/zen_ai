from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Sequence

from ..core.models import Interaction


def load_interactions(path: str | Path) -> Sequence[Interaction]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    interactions: list[Interaction] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {file_path}"
                ) from exc
            interactions.append(_parse_interaction(payload, line_number, file_path))
    return interactions


def _parse_interaction(
    payload: dict,
    line_number: int,
    file_path: Path,
) -> Interaction:
    required = ["user_input", "response_text", "feedback", "refusal"]
    missing = [key for key in required if key not in payload]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(
            f"Missing keys on line {line_number} in {file_path}: {missing_list}"
        )

    feedback = str(payload["feedback"]).strip()
    refusal = bool(payload["refusal"])
    
    return Interaction(
        user_input=str(payload["user_input"]),
        response_text=str(payload["response_text"]),
        feedback=feedback,
        refusal=refusal,
    )
