from signals.base import Signal


class Constant(Signal):
    """Returns a fixed value for any time ``t``."""

    def __init__(self, value: float) -> None:
        self._value = value

    def value(self, t: float) -> float:
        return self._value
