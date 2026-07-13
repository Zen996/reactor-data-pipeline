"""Stage 8 demo: one-shot drain at t=100 + periodic vapor vent every 20s."""

from core.engine import SimulationEngine
from core.process import Recorder
from core.state import ReactorState
from processes.manipulation import (
    DrainReactor,
    InjectSpecies,
    Manipulation,
    ManipulationProcess,
    PeriodicTrigger,
    TimeTrigger,
    VentVapor,
)


class PrintingRecorder(Recorder):
    def record(self, state, sim_time: float) -> None:
        x_liq = state.liquid.get("X", 0.0)
        x_vap = state.vapor.get("X", 0.0)
        print(
            f"t={sim_time:5.1f}  V={state.volume:7.2f}  "
            f"X_liq={x_liq:7.2f}  X_vap={x_vap:7.2f}"
        )


def main() -> None:
    state = ReactorState(volume=100.0, time=0.0)
    state.register_species("X", phase="liquid", initial=100.0)
    state.register_species("X", phase="vapor", initial=10.0)

    manipulations = ManipulationProcess(manipulations=[
        Manipulation(
            trigger=TimeTrigger(time=100.0),
            action=DrainReactor(fraction=0.5),
            one_shot=True,
        ),
        Manipulation(
            trigger=PeriodicTrigger(period=20.0, phase_offset=20.0),
            action=VentVapor(species="X", fraction=0.3),
            one_shot=False,
        ),
        Manipulation(
            trigger=TimeTrigger(time=0.0),
            action=InjectSpecies(phase="liquid", species="X", amount=1.0),
            one_shot=False,
        ),
    ])

    engine = SimulationEngine(
        initial_state=state,
        processes=[manipulations],
        recorder=PrintingRecorder(),
        dt=1.0,
        duration=200.0,
    )
    engine.run()


if __name__ == "__main__":
    main()
