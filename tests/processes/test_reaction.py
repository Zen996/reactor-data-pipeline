"""Tests for ReactionProcess (Stage 6)."""

import pytest

from core.state import ReactorState
from processes.reaction import Reaction, ReactionProcess


class TestReactionProcess:
    """Acceptance criteria for Stage 6's ReactionProcess."""

    def test_stoichiometric_ratio(self) -> None:
        """C1: 2A + B → 3C, changes are in ratio 2:1:3."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=10.0)
        state.register_species("B", initial=10.0)
        state.register_species("C", initial=0.0)

        r = Reaction(
            reactants={"A": 2, "B": 1},
            products={"C": 3},
            rate_constant=0.1,
            phase="liquid",
        )
        process = ReactionProcess(reactions=[r])

        before = state.copy()
        process.execute(state, dt=1.0)

        dA = state.liquid["A"] - before.liquid["A"]
        dB = state.liquid["B"] - before.liquid["B"]
        dC = state.liquid["C"] - before.liquid["C"]

        # Stoichiometric ratio: 2:1:3
        assert dA / 2 == pytest.approx(dB / 1, rel=1e-6)
        assert dA / 2 == pytest.approx(-dC / 3, rel=1e-6)
        assert dA < 0
        assert dC > 0

    def test_uninvolved_species_untouched(self) -> None:
        """C2: A species not in any reaction is unchanged."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=10.0)
        state.register_species("B", initial=5.0)
        state.register_species("Inert", initial=100.0)

        r = Reaction(
            reactants={"A": 1},
            products={"B": 1},
            rate_constant=0.5,
        )
        process = ReactionProcess(reactions=[r])

        inert_before = state.liquid["Inert"]
        process.execute(state, dt=1.0)
        assert state.liquid["Inert"] == inert_before

    def test_two_reactions_shared_species(self) -> None:
        """C3: Two reactions with a shared species — net change is sum,
        independent of list order."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=100.0)
        state.register_species("B", initial=0.0)
        state.register_species("C", initial=0.0)

        r1 = Reaction(
            reactants={"A": 1},
            products={"B": 1},
            rate_constant=0.2,
        )
        r2 = Reaction(
            reactants={"B": 1},
            products={"C": 1},
            rate_constant=0.1,
        )

        # Order 1: [r1, r2]
        s1 = state.copy()
        ReactionProcess(reactions=[r1, r2]).execute(s1, dt=1.0)

        # Order 2: [r2, r1]
        s2 = state.copy()
        ReactionProcess(reactions=[r2, r1]).execute(s2, dt=1.0)

        assert s1.liquid["A"] == pytest.approx(s2.liquid["A"])
        assert s1.liquid["B"] == pytest.approx(s2.liquid["B"])
        assert s1.liquid["C"] == pytest.approx(s2.liquid["C"])

    def test_clamp_negative(self) -> None:
        """C4: Reactant near zero clamps rather than going negative."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=0.5)
        state.register_species("B", initial=10.0)

        # High rate that would drive A negative
        r = Reaction(
            reactants={"A": 2, "B": 1},
            products={},
            rate_constant=10.0,
        )
        process = ReactionProcess(reactions=[r])
        process.execute(state, dt=1.0)

        assert state.liquid["A"] >= 0.0
        assert state.liquid["A"] == pytest.approx(0.0, abs=1e-12)

    def test_order_defaults_to_stoichiometry(self) -> None:
        """C5: order=None uses stoichiometric coefficients as order."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=10.0)
        state.register_species("B", initial=10.0)

        r_default = Reaction(
            reactants={"A": 2, "B": 1},
            products={"C": 1},
            rate_constant=0.05,
            order=None,
        )
        r_explicit = Reaction(
            reactants={"A": 2, "B": 1},
            products={"C": 1},
            rate_constant=0.05,
            order={"A": 2.0, "B": 1.0},
        )

        s_def = state.copy()
        ReactionProcess(reactions=[r_default]).execute(s_def, dt=1.0)

        s_exp = state.copy()
        ReactionProcess(reactions=[r_explicit]).execute(s_exp, dt=1.0)

        assert s_def.liquid["A"] == pytest.approx(s_exp.liquid["A"])

    def test_derived_rates(self) -> None:
        """C6: state.derived contains recognizable rate per reaction."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=10.0)

        r1 = Reaction(reactants={"A": 1}, products={}, rate_constant=0.3)
        r2 = Reaction(reactants={"A": 1}, products={}, rate_constant=0.5)
        process = ReactionProcess(reactions=[r1, r2])

        process.execute(state, dt=1.0)

        assert "reaction_rate_0" in state.derived
        assert "reaction_rate_1" in state.derived
        # Rate = k * [A]^1 = 0.3 * 10 = 3.0, clamped to extent/1
        assert state.derived["reaction_rate_0"] > 0.0
        assert state.derived["reaction_rate_1"] > 0.0

    def test_multiple_steps_depletion(self) -> None:
        """Reaction runs over multiple steps, species depletes toward
        zero asymptotically."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=100.0)
        state.register_species("B", initial=0.0)

        r = Reaction(
            reactants={"A": 1},
            products={"B": 1},
            rate_constant=0.1,
        )
        process = ReactionProcess(reactions=[r])

        for i in range(50):
            state.time = float(i)
            process.execute(state, dt=1.0)

        # A should be nearly depleted, B nearly 100
        assert state.liquid["A"] < 1.0
        assert state.liquid["B"] == pytest.approx(100.0, abs=1.0)

    def test_zero_reactant_does_not_crash(self) -> None:
        """Reaction with a zero-concentration reactant produces zero
        rate, not a crash."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=0.0)
        state.register_species("B", initial=10.0)

        r = Reaction(
            reactants={"A": 1},
            products={"B": 1},
            rate_constant=10.0,
        )
        process = ReactionProcess(reactions=[r])
        process.execute(state, dt=1.0)

        assert state.liquid["A"] == 0.0
        assert state.liquid["B"] == 10.0  # unchanged
