"""Tests for EquilibriumProcess (Stage 7)."""

import pytest

from core.state import ReactorState
from processes.equilibrium import PhaseEquilibrium, EquilibriumProcess


class TestEquilibriumProcess:
    """Acceptance criteria for Stage 7's EquilibriumProcess."""

    def test_evaporation_only(self) -> None:
        """C1: evaporation_coeff > 0, condensation = 0:
        liquid depletes, vapor accumulates monotonically."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("X", phase="liquid", initial=100.0)
        state.register_species("X", phase="vapor", initial=0.0)

        pair = PhaseEquilibrium(species="X", evaporation_coeff=0.1,
                                condensation_coeff=0.0)
        process = EquilibriumProcess(pairs=[pair])

        for i in range(50):
            process.execute(state, dt=1.0)

        assert state.liquid["X"] < 50.0  # at least half evaporated
        assert state.vapor["X"] > 50.0
        # total mass conserved
        assert state.liquid["X"] + state.vapor["X"] == pytest.approx(100.0)

    def test_steady_state(self) -> None:
        """C2: Starting at steady state stays constant."""
        # Steady state: evap_coeff * liq_conc = cond_coeff * vap_conc
        # With volume=1, conc = qty.
        # evap=0.1, cond=0.2 => 0.1 * liq = 0.2 * vap => liq = 2*vap
        # With total = 30: liq = 20, vap = 10
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("X", phase="liquid", initial=20.0)
        state.register_species("X", phase="vapor", initial=10.0)

        pair = PhaseEquilibrium(species="X", evaporation_coeff=0.1,
                                condensation_coeff=0.2)
        process = EquilibriumProcess(pairs=[pair])

        for i in range(100):
            process.execute(state, dt=1.0)

        assert state.liquid["X"] == pytest.approx(20.0, rel=0.02)
        assert state.vapor["X"] == pytest.approx(10.0, rel=0.02)

    def test_condensation(self) -> None:
        """C3: Excess vapor → net transfer to liquid."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("X", phase="liquid", initial=0.0)
        state.register_species("X", phase="vapor", initial=100.0)

        pair = PhaseEquilibrium(species="X", evaporation_coeff=0.0,
                                condensation_coeff=0.1)
        process = EquilibriumProcess(pairs=[pair])

        for i in range(50):
            process.execute(state, dt=1.0)

        assert state.vapor["X"] < 50.0
        assert state.liquid["X"] > 50.0
        assert state.liquid["X"] + state.vapor["X"] == pytest.approx(100.0)

    def test_no_negative_with_large_dt(self) -> None:
        """C4: Aggressive dt doesn't drive any phase negative."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("X", phase="liquid", initial=1.0)
        state.register_species("X", phase="vapor", initial=0.0)

        pair = PhaseEquilibrium(species="X", evaporation_coeff=10.0,
                                condensation_coeff=0.0)
        process = EquilibriumProcess(pairs=[pair])

        process.execute(state, dt=100.0)

        assert state.liquid["X"] >= 0.0
        assert state.vapor["X"] >= 0.0

    def test_auto_register_target_phase(self) -> None:
        """Species auto-registered in target phase if missing."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("X", phase="liquid", initial=100.0)
        # vapor phase not registered

        pair = PhaseEquilibrium(species="X", evaporation_coeff=0.1,
                                condensation_coeff=0.0)
        process = EquilibriumProcess(pairs=[pair])

        process.execute(state, dt=1.0)

        assert "X" in state.vapor
        assert state.vapor["X"] > 0.0

    def test_mass_conservation(self) -> None:
        """Total mass conserved across many steps."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("X", phase="liquid", initial=80.0)
        state.register_species("X", phase="vapor", initial=20.0)

        pair = PhaseEquilibrium(species="X", evaporation_coeff=0.15,
                                condensation_coeff=0.1)
        process = EquilibriumProcess(pairs=[pair])

        for i in range(200):
            process.execute(state, dt=0.5)

        assert state.liquid["X"] + state.vapor["X"] == pytest.approx(100.0, rel=1e-10)
