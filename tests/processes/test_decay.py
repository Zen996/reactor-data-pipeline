"""Tests for DecayProcess (Stage 7)."""

import math

import pytest

from core.state import ReactorState
from processes.decay import DecayRule, DecayProcess


class TestDecayProcess:
    """Acceptance criteria for Stage 7's DecayProcess."""

    def test_exponential_decay_curve(self) -> None:
        """C1: Pure sink decay follows C(t) ≈ C0 * exp(-k*t)."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=100.0)

        rule = DecayRule(species="A", rate_constant=0.1, phase="liquid")
        process = DecayProcess(rules=[rule])

        for i in range(50):
            state.time = float(i)
            process.execute(state, dt=0.1)

        expected = 100.0 * math.exp(-0.1 * 5.0)  # 50 * 0.1 = 5 sec
        assert state.liquid["A"] == pytest.approx(expected, rel=0.02)

    def test_decay_with_products(self) -> None:
        """C2: Decay C → 2A follows 1:2 stoichiometry."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("C", initial=50.0)
        state.register_species("A", initial=0.0)

        rule = DecayRule(species="C", rate_constant=0.2, phase="liquid",
                         products={"A": 2})
        process = DecayProcess(rules=[rule])

        before = state.copy()
        process.execute(state, dt=1.0)

        dC = state.liquid["C"] - before.liquid["C"]
        dA = state.liquid["A"] - before.liquid["A"]

        assert dC < 0
        assert dA > 0
        # C decreases by extent*vol, A increases by 2*extent*vol
        # So dA = -2 * dC
        assert dA == pytest.approx(-2.0 * dC, rel=1e-6)

    def test_clamp_zero(self) -> None:
        """C3: Clamps at zero rather than going negative."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=1.0)

        rule = DecayRule(species="A", rate_constant=100.0)
        process = DecayProcess(rules=[rule])

        process.execute(state, dt=10.0)

        assert state.liquid["A"] == pytest.approx(0.0, abs=1e-12)
        assert state.liquid["A"] >= 0.0

    def test_multiple_rules_same_species(self) -> None:
        """Multiple decay rules affecting same species accumulate."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=100.0)
        state.register_species("B", initial=0.0)

        rule1 = DecayRule(species="A", rate_constant=0.1, products={"B": 1})
        rule2 = DecayRule(species="A", rate_constant=0.2, products={"B": 1})
        process = DecayProcess(rules=[rule1, rule2])

        before = state.copy()
        process.execute(state, dt=1.0)

        dA = before.liquid["A"] - state.liquid["A"]
        dB = state.liquid["B"] - before.liquid["B"]

        # Both rates computed from start-of-step state (A=100):
        #   Rule1: k=0.1 → extent=10 → A -= 10, B += 10
        #   Rule2: k=0.2 → extent=20 → A -= 20, B += 20
        #   Total: A=70, B=30
        assert state.liquid["A"] == pytest.approx(70.0, rel=0.01)
        assert state.liquid["B"] == pytest.approx(30.0, rel=0.01)

    def test_zero_rate_no_change(self) -> None:
        """Zero rate constant produces no change."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=100.0)

        rule = DecayRule(species="A", rate_constant=0.0)
        process = DecayProcess(rules=[rule])

        process.execute(state, dt=1.0)
        assert state.liquid["A"] == 100.0
