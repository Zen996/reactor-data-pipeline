from signals.base import Signal


class Ramp(Signal):
    """Linear ramp, optionally clamped to [min_value, max_value].

    Returns ``start_value`` for ``t < start_time``, then
    ``start_value + slope * (t - start_time)``, bounded by
    ``[min_value, max_value]`` when provided.
    """

    def __init__(
        self,
        start_value: float,
        slope: float,
        start_time: float = 0.0,
        max_value: float | None = None,
        min_value: float | None = None,
    ) -> None:
        self._start_value = start_value
        self._slope = slope
        self._start_time = start_time
        self._max_value = max_value
        self._min_value = min_value

    def value(self, t: float) -> float:
        if t < self._start_time:
            v = self._start_value
        else:
            v = self._start_value + self._slope * (t - self._start_time)

        if self._min_value is not None and v < self._min_value:
            v = self._min_value
        if self._max_value is not None and v > self._max_value:
            v = self._max_value
        return v
