from __future__ import annotations

import bisect
from dataclasses import dataclass


@dataclass
class Checkpoint:
    time: float
    state: "ReactorState"


class CheckpointStore:
    """Time-ordered list of ReactorState snapshots, one per recorded step."""

    def __init__(self) -> None:
        self._checkpoints: list[Checkpoint] = []

    def add(self, time: float, state: "ReactorState") -> None:
        cp = Checkpoint(time=time, state=state.copy())
        self._checkpoints.append(cp)

    def nearest_at_or_before(self, time: float) -> Checkpoint | None:
        if not self._checkpoints:
            return None
        times = [cp.time for cp in self._checkpoints]
        idx = bisect.bisect_right(times, time) - 1
        if idx < 0:
            return None
        return self._checkpoints[idx]

    def drop_after(self, time: float) -> None:
        self._checkpoints = [cp for cp in self._checkpoints if cp.time <= time]
