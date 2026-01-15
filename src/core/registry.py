from __future__ import annotations

from dataclasses import dataclass

from .models import PromptSnapshot


@dataclass
class PromptRegistry:
    snapshots: list[PromptSnapshot]

    def latest(self) -> PromptSnapshot:
        if not self.snapshots:
            raise RuntimeError("Prompt registry is empty.")
        return self.snapshots[-1]

    def append(self, snapshot: PromptSnapshot) -> None:
        self.snapshots.append(snapshot)

    def rollback(self) -> PromptSnapshot:
        if len(self.snapshots) < 2:
            raise RuntimeError("No previous snapshot to rollback to.")
        self.snapshots.pop()
        return self.latest()
