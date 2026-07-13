"""Full-stack reproducibility test (Stage 9).

Build a small end-to-end simulation with mixing + reaction + sensor noise,
run it twice with the same seed, and assert byte-identical recorded rows.
"""

from core.engine import SimulationEngine
from core.process import Recorder
from core.random_manager import RandomManager
from core.state import ReactorState
from core.stream import InputStream
from processes.mixing import MixingProcess
from processes.reaction import Reaction, ReactionProcess
from processes.sensors import SensorNoiseProcess, SensorSpec
from signals.constant import Constant
from signals.noise import GaussianNoise


class ListRecorder(Recorder):
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def record(self, state, sim_time: float) -> None:
        row = dict(state.snapshot())
        row.update(state.derived)
        self.rows.append(row)

    def finalize(self) -> None:
        pass


def build_simulation(seed: int) -> tuple[ListRecorder, SimulationEngine]:
    """Create a small simulation with mixing, reaction, and sensor noise."""
    rm = RandomManager(seed)

    state = ReactorState(volume=100.0, time=0.0)
    state.register_species("A", initial=50.0)
    state.register_species("B", initial=0.0)
    state.register_species("C", initial=0.0)

    feed = InputStream(
        name="Feed A",
        flow_signal=Constant(5.0),
        composition={"A": Constant(2.0)},
    )

    reaction = Reaction(
        reactants={"A": 1},
        products={"B": 1},
        rate_constant=0.02,
    )

    sensor = SensorSpec(
        species="B",
        phase="liquid",
        noise=GaussianNoise(mean=0.0, std=0.5, generator=rm.spawn("sensor.B")),
        output_key="sensor.B",
    )

    processes = [
        MixingProcess(streams=[feed]),
        ReactionProcess(reactions=[reaction]),
        SensorNoiseProcess(sensors=[sensor]),
    ]

    recorder = ListRecorder()
    engine = SimulationEngine(
        initial_state=state,
        processes=processes,
        recorder=recorder,
        dt=1.0,
        duration=20.0,
    )
    return recorder, engine


class TestReproducibility:
    def test_identical_seed_identical_output(self) -> None:
        """Two runs with the same seed produce identical recorded data."""
        rec1, eng1 = build_simulation(42)
        eng1.run()

        rec2, eng2 = build_simulation(42)
        eng2.run()

        for row1, row2 in zip(rec1.rows, rec2.rows):
            for key in row1:
                assert row1[key] == row2[key], (
                    f"Mismatch at key={key}: {row1[key]} != {row2[key]}"
                )

    def test_different_seeds_diverge(self) -> None:
        """Different seeds produce different sensor readings but
        deterministic state variables match (noise is additive)."""
        rec1, eng1 = build_simulation(42)
        eng1.run()

        rec2, eng2 = build_simulation(99)
        eng2.run()

        # Deterministic state fields should match
        deterministic_keys = {"time", "volume", "liquid.A", "liquid.B", "outflow_rate"}

        for row1, row2 in zip(rec1.rows, rec2.rows):
            for key in deterministic_keys:
                if key in row1:
                    assert row1[key] == row2[key], (
                        f"Deterministic field {key} differs: {row1[key]} != {row2[key]}"
                    )

        # Sensor readings should differ (overwhelmingly likely)
        sensor_vals_1 = [r.get("sensor.B", 0.0) for r in rec1.rows]
        sensor_vals_2 = [r.get("sensor.B", 0.0) for r in rec2.rows]
        assert sensor_vals_1 != sensor_vals_2
