from signals.base import Signal


class Step(Signal):
    """Piecewise constant with a single step at *step_time*.

    Returns ``baseline`` for ``t < step_time``, ``step_value`` otherwise.
    """

    def __init__(self, baseline: float, step_value: float, step_time: float) -> None:
        self._baseline = baseline
        self._step_value = step_value
        self._step_time = step_time

    def value(self, t: float) -> float:
        if t < self._step_time:
            return self._baseline
        return self._step_value
