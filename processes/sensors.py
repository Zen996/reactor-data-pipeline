"""Sensor noise process — additive measurement noise to state.derived.

This process **must not** modify ``state.liquid`` or ``state.vapor``.
It represents measurement artefacts, not physical changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.process import Process
from signals.base import Signal


@dataclass
class SensorSpec:
    """Configuration for one noisy sensor reading.

    Parameters
    ----------
    species:
        The species to measure.
    phase:
        Which phase the measurement is taken from.
    noise:
        A noise Signal (typically :class:`~signals.noise.GaussianNoise` or
        ``UniformNoise``).
    output_key:
        Key under which the noisy reading is stored in ``state.derived``.
    """

    species: str
    phase: str
    noise: Signal
    output_key: str


class SensorNoiseProcess(Process):
    """Apply additive sensor noise to simulated measurements.

    For each sensor, the true quantity is read from the state and the
    noisy reading is written to ``state.derived[output_key]``.  The
    underlying state quantities are **never** modified.
    """

    def __init__(self, sensors: list[SensorSpec]) -> None:
        self._sensors = list(sensors)

    def execute(self, state, dt: float) -> None:
        for sensor in self._sensors:
            true_value = state.get(sensor.species, phase=sensor.phase)
            noise_value = sensor.noise.value(state.time)
            state.derived[sensor.output_key] = true_value + noise_value
