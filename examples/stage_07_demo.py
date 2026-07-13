"""Stage 7 demo: decay (C → 2A) + liquid/vapor equilibrium (X) in one run."""

from core.engine import SimulationEngine
from core.process import Recorder
from core.state import ReactorState
from processes.decay import DecayRule, DecayProcess
from processes.equilibrium import PhaseEquilibrium, EquilibriumProcess


class PrintingRecorder(Recorder):
    def record(self, state, sim_time: float) -> None:
        a = state.liquid.get("A", 0.0)
        c = state.liquid.get("C", 0.0)
        x_liq = state.liquid.get("X", 0.0)
        x_vap = state.vapor.get("X", 0.0)
        print(
            f"t={sim_time:5.1f}  C={c:7.2f}  A={a:7.2f}  "
            f"X_liq={x_liq:7.2f}  X_vap={x_vap:7.2f}"
        )


def main() -> None:
    state = ReactorState(volume=10.0, time=0.0)
    state.register_species("C", initial=100.0)
    state.register_species("A", initial=0.0)
    state.register_species("X", phase="liquid", initial=80.0)
    state.register_species("X", phase="vapor", initial=20.0)

    decay = DecayProcess(rules=[
        DecayRule(species="C", rate_constant=0.05, products={"A": 2}),
    ])
    equilibrium = EquilibriumProcess(pairs=[
        PhaseEquilibrium(species="X", evaporation_coeff=0.1,
                         condensation_coeff=0.15),
    ])

    engine = SimulationEngine(
        initial_state=state,
        processes=[decay, equilibrium],
        recorder=PrintingRecorder(),
        dt=1.0,
        duration=60.0,
    )
    engine.run()


if __name__ == "__main__":
    main()
