"""Tests for SensorNoiseProcess (Stage 9)."""

import numpy as np

from core.random_manager import RandomManager
from core.state import ReactorState
from processes.sensors import SensorNoiseProcess, SensorSpec
from signals.noise import GaussianNoise, UniformNoise


class TestSensorNoiseProcess:
    """Acceptance criteria for Stage 9's SensorNoiseProcess."""

    def test_does_not_mutate_state(self) -> None:
        """C1a: state.liquid/vapor are unchanged after execute()."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=100.0)

        liq_before = dict(state.liquid)
        vap_before = dict(state.vapor)

        spec = SensorSpec(
            species="A",
            phase="liquid",
            noise=GaussianNoise(mean=0.0, std=5.0, seed=42),
            output_key="sensor.A",
        )
        process = SensorNoiseProcess(sensors=[spec])

        process.execute(state, dt=1.0)

        assert state.liquid == liq_before
        assert state.vapor == vap_before

    def test_derived_contains_noisy_value(self) -> None:
        """C1b: state.derived[output_key] differs from true value when
        std > 0."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=100.0)

        spec = SensorSpec(
            species="A",
            phase="liquid",
            noise=GaussianNoise(mean=0.0, std=10.0, seed=42),
            output_key="sensor.A",
        )
        process = SensorNoiseProcess(sensors=[spec])

        process.execute(state, dt=1.0)

        assert "sensor.A" in state.derived
        assert state.derived["sensor.A"] != 100.0

    def test_same_seed_identical_readings(self) -> None:
        """C2: Same seed → identical derived values across two runs."""
        reads = []
        for _ in range(2):
            state = ReactorState(volume=1.0, time=0.0)
            state.register_species("A", initial=50.0)

            spec = SensorSpec(
                species="A",
                phase="liquid",
                noise=GaussianNoise(mean=0.0, std=2.0, seed=42),
                output_key="sensor.A",
            )
            process = SensorNoiseProcess(sensors=[spec])
            process.execute(state, dt=1.0)
            reads.append(state.derived["sensor.A"])

        assert reads[0] == reads[1]

    def test_multiple_sensors_independent(self) -> None:
        """Multiple sensors produce independent readings."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=100.0)
        state.register_species("B", initial=200.0)

        rm = RandomManager(seed=42)
        specs = [
            SensorSpec(
                species="A", phase="liquid",
                noise=GaussianNoise(mean=0.0, std=1.0, generator=rm.spawn("sensor.A")),
                output_key="sensor.A",
            ),
            SensorSpec(
                species="B", phase="liquid",
                noise=GaussianNoise(mean=0.0, std=2.0, generator=rm.spawn("sensor.B")),
                output_key="sensor.B",
            ),
        ]
        process = SensorNoiseProcess(sensors=specs)
        process.execute(state, dt=1.0)

        assert "sensor.A" in state.derived
        assert "sensor.B" in state.derived
        assert state.derived["sensor.A"] != state.derived["sensor.B"]
