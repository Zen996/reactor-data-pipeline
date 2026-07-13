"""Tests for ManipulationProcess (Stage 8)."""

from types import SimpleNamespace

import pytest

from core.state import ReactorState
from processes.manipulation import (
    DrainReactor,
    InjectSpecies,
    Manipulation,
    ManipulationProcess,
    ManualTrigger,
    PeriodicTrigger,
    RemoveSpecies,
    ThresholdTrigger,
    TimeTrigger,
    VentVapor,
)


class TestTimeTrigger:
    def test_one_shot_injects_once(self) -> None:
        """C1: TimeTrigger + one_shot=True + InjectSpecies fires exactly
        once at/after the configured time."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=0.0)

        m = Manipulation(
            trigger=TimeTrigger(time=5.0),
            action=InjectSpecies(phase="liquid", species="A", amount=10.0),
            one_shot=True,
        )
        process = ManipulationProcess(manipulations=[m])

        for t in range(20):
            state.time = float(t)
            process.execute(state, dt=1.0)

        # A should be exactly 10.0 (injected once at t=5)
        assert state.liquid["A"] == pytest.approx(10.0)

    def test_continuous_injection(self) -> None:
        """C2: TimeTrigger + one_shot=False fires every step from
        configured time onward."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=0.0)

        m = Manipulation(
            trigger=TimeTrigger(time=10.0),
            action=InjectSpecies(phase="liquid", species="A", amount=5.0),
            one_shot=False,
        )
        process = ManipulationProcess(manipulations=[m])

        for t in range(20):
            state.time = float(t)
            process.execute(state, dt=1.0)

        # Injected at t=10, 11, ..., 19 = 10 times × 5 = 50
        assert state.liquid["A"] == pytest.approx(50.0)


class TestThresholdTrigger:
    def test_fires_once_past_threshold(self) -> None:
        """C3: ThresholdTrigger fires once past the crossing point with
        one_shot=True."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=0.0)
        state.register_species("B", initial=0.0)

        m = Manipulation(
            trigger=ThresholdTrigger(
                species="A", phase="liquid", comparator="gt", value=50.0
            ),
            action=InjectSpecies(phase="liquid", species="B", amount=100.0),
            one_shot=True,
        )
        process = ManipulationProcess(manipulations=[m])

        # Manually increase A over time to cross threshold at t=6
        for t in range(20):
            state.time = float(t)
            state.liquid["A"] = t * 10.0  # 0, 10, 20, ..., 190
            process.execute(state, dt=1.0)

        # B should be injected exactly once (when A > 50 at t=6)
        assert state.liquid.get("B", 0.0) == pytest.approx(100.0)

    def test_invalid_comparator_raises(self) -> None:
        """C4: Invalid comparator string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid comparator"):
            ThresholdTrigger(
                species="A", phase="liquid", comparator="invalid", value=10.0
            )

    def test_valid_comparators(self) -> None:
        """All four valid comparators work at construction."""
        for cmp in ("gt", "lt", "ge", "le"):
            t = ThresholdTrigger(species="A", phase="liquid", comparator=cmp, value=10.0)
            assert t.comparator == cmp


class TestPeriodicTrigger:
    def test_firing_count(self) -> None:
        """C5: PeriodicTrigger fires approximately duration/period times."""
        state = SimpleNamespace(time=0.0)
        trigger = PeriodicTrigger(period=10.0, phase_offset=0.0)
        count = 0
        for i in range(200):
            state.time = float(i)
            if trigger.is_active(state):
                count += 1
        # Fires at t=0, 10, 20, ..., 190 = 20 times
        assert count == 20

    def test_with_phase_offset(self) -> None:
        """Phase offset shifts first fire."""
        state = SimpleNamespace(time=0.0)
        trigger = PeriodicTrigger(period=10.0, phase_offset=5.0)
        count = 0
        for i in range(100):
            state.time = float(i)
            if trigger.is_active(state):
                count += 1
        # Fires at t=5, 15, 25, ..., 95 = 10 times
        assert count == 10


class TestManualTrigger:
    def test_fire_once_per_call(self) -> None:
        """ManualTrigger fires once per fire() call."""
        trigger = ManualTrigger()
        state = SimpleNamespace(time=0.0)

        assert not trigger.is_active(state)

        trigger.fire()
        assert trigger.is_active(state)
        assert not trigger.is_active(state)  # consumed

        trigger.fire()
        trigger.fire()
        assert trigger.is_active(state)  # one consumed
        assert not trigger.is_active(state)  # second consumed


class TestActions:
    def test_drain_reactor(self) -> None:
        """C6: DrainReactor(fraction=0.5) halves volume and every liquid
        species; concentrations unchanged."""
        state = ReactorState(volume=100.0, time=0.0)
        state.register_species("A", initial=60.0)
        state.register_species("B", initial=40.0)
        state.register_species("C", phase="vapor", initial=50.0)

        action = DrainReactor(fraction=0.5)
        action.apply(state, dt=1.0)

        assert state.volume == pytest.approx(50.0)
        assert state.liquid["A"] == pytest.approx(30.0)
        assert state.liquid["B"] == pytest.approx(20.0)
        # Vapor untouched
        assert state.vapor["C"] == pytest.approx(50.0)
        # Concentrations unchanged
        assert state.liquid["A"] / state.volume == pytest.approx(60.0 / 100.0)
        assert state.liquid["B"] / state.volume == pytest.approx(40.0 / 100.0)

    def test_vent_vapor_all(self) -> None:
        """C7: VentVapor(species=None, fraction=1.0) clears all vapor;
        liquid untouched."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("X", phase="vapor", initial=30.0)
        state.register_species("Y", phase="vapor", initial=20.0)
        state.register_species("Z", phase="liquid", initial=100.0)

        action = VentVapor(species=None, fraction=1.0)
        action.apply(state, dt=1.0)

        assert state.vapor["X"] == pytest.approx(0.0)
        assert state.vapor["Y"] == pytest.approx(0.0)
        assert state.liquid["Z"] == pytest.approx(100.0)

    def test_vent_vapor_specific(self) -> None:
        """VentVapor with species name only affects that species."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("X", phase="vapor", initial=30.0)
        state.register_species("Y", phase="vapor", initial=20.0)

        action = VentVapor(species="X", fraction=0.5)
        action.apply(state, dt=1.0)

        assert state.vapor["X"] == pytest.approx(15.0)
        assert state.vapor["Y"] == pytest.approx(20.0)

    def test_remove_species_clamps(self) -> None:
        """C8: RemoveSpecies requesting more than available clamps to
        zero."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=5.0)

        action = RemoveSpecies(phase="liquid", species="A", amount=100.0)
        action.apply(state, dt=1.0)

        assert state.liquid["A"] == pytest.approx(0.0)
        assert state.liquid["A"] >= 0.0

    def test_remove_species_partial(self) -> None:
        """RemoveSpecies removes the correct amount when feasible."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=20.0)

        action = RemoveSpecies(phase="liquid", species="A", amount=8.0)
        action.apply(state, dt=1.0)

        assert state.liquid["A"] == pytest.approx(12.0)

    def test_inject_species(self) -> None:
        """InjectSpecies adds to the correct phase."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=10.0)

        action = InjectSpecies(phase="liquid", species="A", amount=25.0)
        action.apply(state, dt=1.0)

        assert state.liquid["A"] == pytest.approx(35.0)

    def test_drain_fraction_above_one(self) -> None:
        """Drain with fraction > 1 clamps to draining everything."""
        state = ReactorState(volume=100.0, time=0.0)
        state.register_species("A", initial=50.0)

        action = DrainReactor(fraction=2.0)
        action.apply(state, dt=1.0)

        assert state.volume == pytest.approx(0.0, abs=1e-12)


class TestManipulationProcess:
    def test_multiple_manipulations(self) -> None:
        """Multiple manipulations are evaluated independently."""
        state = ReactorState(volume=1.0, time=0.0)
        state.register_species("A", initial=0.0)
        state.register_species("B", initial=0.0)

        manip_a = Manipulation(
            trigger=TimeTrigger(time=5.0),
            action=InjectSpecies(phase="liquid", species="A", amount=10.0),
            one_shot=True,
        )
        manip_b = Manipulation(
            trigger=TimeTrigger(time=10.0),
            action=InjectSpecies(phase="liquid", species="B", amount=20.0),
            one_shot=False,
        )
        process = ManipulationProcess(manipulations=[manip_a, manip_b])

        for t in range(20):
            state.time = float(t)
            process.execute(state, dt=1.0)

        # A: one shot at t=5 → 10
        # B: continuous from t=10 → 10 steps × 20 = 200
        assert state.liquid["A"] == pytest.approx(10.0)
        assert state.liquid["B"] == pytest.approx(200.0)
