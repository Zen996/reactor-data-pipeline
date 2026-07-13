"""Stage 6 demo: 2A + B → 3C, run via the Stage 1 engine."""

from core.engine import SimulationEngine
from core.process import Recorder
from core.state import ReactorState
from processes.reaction import Reaction, ReactionProcess


class PrintingRecorder(Recorder):
    def record(self, state, sim_time: float) -> None:
        a = state.liquid.get("A", 0.0)
        b = state.liquid.get("B", 0.0)
        c = state.liquid.get("C", 0.0)
        print(f"t={sim_time:5.1f}  A={a:8.3f}  B={b:8.3f}  C={c:8.3f}")


def main() -> None:
    state = ReactorState(volume=10.0, time=0.0)
    state.register_species("A", initial=100.0)
    state.register_species("B", initial=50.0)
    state.register_species("C", initial=0.0)

    r = Reaction(
        reactants={"A": 2, "B": 1},
        products={"C": 3},
        rate_constant=0.002,
        phase="liquid",
    )
    process = ReactionProcess(reactions=[r])

    engine = SimulationEngine(
        initial_state=state,
        processes=[process],
        recorder=PrintingRecorder(),
        dt=1.0,
        duration=100.0,
    )
    engine.run()


if __name__ == "__main__":
    main()
