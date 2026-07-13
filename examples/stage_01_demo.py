"""Stage 1 demo: bare-bones engine with a fake state, one Process, and a
printing Recorder."""

from types import SimpleNamespace

from core.process import Process, Recorder


class AddProcess(Process):
    """Adds 1.0 * dt to state.value each step."""

    def execute(self, state, dt: float) -> None:
        state.value += 1.0 * dt


class PrintingRecorder(Recorder):
    """Prints (sim_time, state.value) to console."""

    def record(self, state, sim_time: float) -> None:
        print(f"t={sim_time:.1f}, value={state.value:.2f}")


def main() -> None:
    from core.engine import SimulationEngine

    state = SimpleNamespace(time=0.0, value=0.0)
    engine = SimulationEngine(
        initial_state=state,
        processes=[AddProcess()],
        recorder=PrintingRecorder(),
        dt=1.0,
        duration=5.0,
    )
    engine.run()

    print(f"\nFinal state: time={state.time}, value={state.value}")


if __name__ == "__main__":
    main()
