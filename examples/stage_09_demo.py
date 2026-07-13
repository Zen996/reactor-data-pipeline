"""Stage 9 demo: run the same simulation with seed=42 twice and seed=7 once,
showing reproducibility of seed 42 and divergence with seed 7."""

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


class DictRecorder(Recorder):
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def record(self, state, sim_time: float) -> None:
        row = dict(state.snapshot())
        row.update(state.derived)
        self.rows.append(row)

    def finalize(self) -> None:
        pass


def run_simulation(seed: int, label: str) -> list[dict]:
    rm = RandomManager(seed)

    state = ReactorState(volume=100.0, time=0.0)
    state.register_species("A", initial=50.0)
    state.register_species("B", initial=0.0)

    feed = InputStream(
        name="Feed A",
        flow_signal=Constant(5.0),
        composition={"A": Constant(2.0)},
    )
    reaction = Reaction(
        reactants={"A": 1}, products={"B": 1}, rate_constant=0.02,
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

    recorder = DictRecorder()
    engine = SimulationEngine(
        initial_state=state,
        processes=processes,
        recorder=recorder,
        dt=1.0,
        duration=10.0,
    )
    engine.run()
    return recorder.rows


def main() -> None:
    rows_42a = run_simulation(42, "seed=42 (run 1)")
    rows_42b = run_simulation(42, "seed=42 (run 2)")
    rows_7 = run_simulation(7, "seed=7")

    print(f"{'t':>4s}  {'B(true)':>8s}  {'B(sensor) seed=42a':>18s}  "
          f"{'B(sensor) seed=42b':>18s}  {'B(sensor) seed=7':>16s}")
    print("-" * 75)
    for i in range(len(rows_42a)):
        print(
            f"{rows_42a[i]['time']:4.0f}  "
            f"{rows_42a[i].get('liquid.B', 0.0):8.2f}  "
            f"{rows_42a[i].get('sensor.B', 0.0):18.6f}  "
            f"{rows_42b[i].get('sensor.B', 0.0):18.6f}  "
            f"{rows_7[i].get('sensor.B', 0.0):16.6f}"
        )

    match_42 = all(
        rows_42a[i].get("sensor.B") == rows_42b[i].get("sensor.B")
        for i in range(len(rows_42a))
    )
    print(f"\nseed=42 runs match: {match_42}")
    print(f"seed=42 ≠ seed=7 (sensor): {rows_42a != rows_7}")


if __name__ == "__main__":
    main()
