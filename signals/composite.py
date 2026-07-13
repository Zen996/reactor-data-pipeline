from signals.base import Signal


class CompositeSignal(Signal):
    """Time-multiplexed signal built from a list of (start, end, signal)
    segments.

    Segments must be sorted by start time and non-overlapping. The
    sub-signal receives the **global** simulation time ``t`` (not
    ``t - segment_start``).

    If ``t`` falls in a gap or before/after all segments, a
    ``ValueError`` is raised.
    """

    def __init__(self, segments: list[tuple[float, float, Signal]]) -> None:
        if not segments:
            raise ValueError("At least one segment is required")

        sorted_segments = sorted(segments, key=lambda s: s[0])

        for i in range(len(sorted_segments) - 1):
            _, end_current, _ = sorted_segments[i]
            start_next, _, _ = sorted_segments[i + 1]
            if start_next < end_current:
                raise ValueError(
                    f"Segments overlap: segment {i} ends at {end_current} "
                    f"but segment {i + 1} starts at {start_next}"
                )

        self._segments = sorted_segments

    def value(self, t: float) -> float:
        for start, end, signal in self._segments:
            if start <= t < end:
                return signal.value(t)

        raise ValueError(
            f"No active segment at t={t}; "
            f"segments cover [{self._segments[0][0]}, {self._segments[-1][1]})"
        )
