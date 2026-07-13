import math

from signals.base import Signal


class Sinusoid(Signal):
    """Sine wave: ``offset + amplitude * sin(2*pi*frequency*t + phase)``.

    When *rectified* is ``True``, takes ``abs()`` of the sinusoid before
    adding the offset, producing a signal that never dips below ``offset``.
    """

    def __init__(
        self,
        amplitude: float,
        frequency: float,
        phase: float = 0.0,
        offset: float = 0.0,
        rectified: bool = False,
    ) -> None:
        self._amplitude = amplitude
        self._frequency = frequency
        self._phase = phase
        self._offset = offset
        self._rectified = rectified

    def value(self, t: float) -> float:
        raw = self._amplitude * math.sin(
            2.0 * math.pi * self._frequency * t + self._phase
        )
        if self._rectified:
            raw = abs(raw)
        return raw + self._offset


class SquareWave(Signal):
    """Square wave with configurable duty cycle.

    Returns ``offset + amplitude`` for (duty_cycle × period) and
    ``offset - amplitude`` for the remainder.
    """

    def __init__(
        self,
        amplitude: float,
        frequency: float,
        duty_cycle: float = 0.5,
        offset: float = 0.0,
    ) -> None:
        self._amplitude = amplitude
        self._frequency = frequency
        self._duty_cycle = duty_cycle
        self._offset = offset

    def value(self, t: float) -> float:
        period = 1.0 / self._frequency
        phase_in_period = t % period
        if phase_in_period < self._duty_cycle * period:
            return self._offset + self._amplitude
        return self._offset - self._amplitude


class TriangleWave(Signal):
    """Triangle wave: linear rise then fall within each period.

    Returns ``offset + amplitude`` at the midpoint of the rising edge and
    ``offset - amplitude`` at the midpoint of the falling edge.
    """

    def __init__(
        self,
        amplitude: float,
        frequency: float,
        offset: float = 0.0,
    ) -> None:
        self._amplitude = amplitude
        self._frequency = frequency
        self._offset = offset

    def value(self, t: float) -> float:
        period = 1.0 / self._frequency
        phase_in_period = t % period
        half_period = period / 2.0

        if phase_in_period < half_period:
            fraction = phase_in_period / half_period
            return self._offset + self._amplitude * (2.0 * fraction - 1.0)
        else:
            fraction = (phase_in_period - half_period) / half_period
            return self._offset + self._amplitude * (1.0 - 2.0 * fraction)
