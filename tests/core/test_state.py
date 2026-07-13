"""Tests for ReactorState (Stage 2)."""

import pytest

from core.state import ReactorState


class TestReactorState:
    """Acceptance criteria for Stage 2's ReactorState."""

    def test_register_and_roundtrip_liquid(self) -> None:
        """C1a: register_species then get/set/add round-trip in liquid phase."""
        state = ReactorState()
        state.register_species("A", phase="liquid", initial=10.0)
        assert state.get("A", phase="liquid") == 10.0

        state.set("A", 20.0, phase="liquid")
        assert state.get("A", phase="liquid") == 20.0

        state.add("A", 5.0, phase="liquid")
        assert state.get("A", phase="liquid") == 25.0

    def test_register_and_roundtrip_vapor(self) -> None:
        """C1b: register_species then get/set/add round-trip in vapor phase."""
        state = ReactorState()
        state.register_species("B", phase="vapor", initial=5.0)
        assert state.get("B", phase="vapor") == 5.0

        state.set("B", 10.0, phase="vapor")
        assert state.get("B", phase="vapor") == 10.0

        state.add("B", -2.0, phase="vapor")
        assert state.get("B", phase="vapor") == 8.0

    def test_get_unregistered_raises(self) -> None:
        """C2: get() on a never-registered species raises KeyError."""
        state = ReactorState()
        with pytest.raises(KeyError, match="not found"):
            state.get("NONEXISTENT", phase="liquid")

        with pytest.raises(KeyError, match="not found"):
            state.get("NONEXISTENT", phase="vapor")

    def test_concentration(self) -> None:
        """C3: concentration() returns quantity / volume."""
        state = ReactorState(volume=2.0)
        state.register_species("A", phase="liquid", initial=10.0)
        state.register_species("B", phase="vapor", initial=6.0)

        assert state.concentration("A", phase="liquid") == 5.0
        assert state.concentration("B", phase="vapor") == 3.0

    def test_concentration_default_volume(self) -> None:
        """concentration works with default volume of 1.0."""
        state = ReactorState()
        state.register_species("A", initial=7.0)
        assert state.concentration("A") == 7.0

    def test_total_mass_both_phases(self) -> None:
        """C4a: total_mass(phase=None) sums liquid and vapor."""
        state = ReactorState()
        state.register_species("A", phase="liquid", initial=10.0)
        state.register_species("B", phase="liquid", initial=5.0)
        state.register_species("C", phase="vapor", initial=3.0)

        assert state.total_mass(phase=None) == 18.0

    def test_total_mass_single_phase(self) -> None:
        """C4b: total_mass(phase='liquid') sums only liquid."""
        state = ReactorState()
        state.register_species("A", phase="liquid", initial=10.0)
        state.register_species("B", phase="vapor", initial=3.0)

        assert state.total_mass(phase="liquid") == 10.0
        assert state.total_mass(phase="vapor") == 3.0

    def test_snapshot_keys(self) -> None:
        """C5: snapshot() returns expected flat dict keys."""
        state = ReactorState(time=5.0, volume=2.5, outflow_rate=0.5)
        state.register_species("A", phase="liquid", initial=10.0)
        state.register_species("B", phase="liquid", initial=20.0)
        state.register_species("C", phase="vapor", initial=3.0)
        state.derived["rate_1"] = 42.0
        state.derived["temp"] = 350.0
        state.inflows["A"] = 99.0  # should NOT appear in snapshot
        state.metadata["run_id"] = "test"  # should NOT appear in snapshot

        snap = state.snapshot()

        assert snap["time"] == 5.0
        assert snap["volume"] == 2.5
        assert snap["outflow_rate"] == 0.5
        assert snap["liquid.A"] == 10.0
        assert snap["liquid.B"] == 20.0
        assert snap["vapor.C"] == 3.0
        assert snap["derived.rate_1"] == 42.0
        assert snap["derived.temp"] == 350.0

        assert "inflows" not in snap
        assert "metadata" not in snap
        assert "A" not in snap  # bare species names should not appear

    def test_snapshot_empty_state(self) -> None:
        """snapshot works on a bare-minimum state."""
        state = ReactorState()
        snap = state.snapshot()
        assert snap == {"time": 0.0, "volume": 1.0, "outflow_rate": 0.0}

    def test_copy_independence(self) -> None:
        """C6: copy() produces an independent deep copy."""
        state = ReactorState()
        state.register_species("A", phase="liquid", initial=10.0)
        state.register_species("B", phase="vapor", initial=5.0)
        state.derived["rate"] = 1.0

        copied = state.copy()

        assert copied.get("A") == 10.0
        assert copied.get("B", phase="vapor") == 5.0
        assert copied.derived["rate"] == 1.0

        copied.add("A", 100.0)
        copied.liquid["B"] = 999  # register via direct dict mutation
        copied.derived["rate"] = 99.0

        assert state.get("A") == 10.0
        assert "B" not in state.liquid
        assert state.derived["rate"] == 1.0

    def test_invalid_phase_raises(self) -> None:
        """C7: every accessor that takes phase raises ValueError for bad phase."""
        state = ReactorState()

        with pytest.raises(ValueError, match="Invalid phase"):
            state.get("A", phase="solid")

        with pytest.raises(ValueError, match="Invalid phase"):
            state.set("A", 1.0, phase="solid")

        with pytest.raises(ValueError, match="Invalid phase"):
            state.add("A", 1.0, phase="solid")

        with pytest.raises(ValueError, match="Invalid phase"):
            state.concentration("A", phase="solid")

        with pytest.raises(ValueError, match="Invalid phase"):
            state.total_mass(phase="solid")

        with pytest.raises(ValueError, match="Invalid phase"):
            state.register_species("A", phase="solid")

    def test_register_initial_zero(self) -> None:
        """register_species with default initial=0.0 works."""
        state = ReactorState()
        state.register_species("A", phase="liquid")
        assert state.get("A") == 0.0

    def test_add_raises_if_not_registered(self) -> None:
        """add() on an unregistered species raises KeyError."""
        state = ReactorState()
        with pytest.raises(KeyError, match="Species 'A' not found"):
            state.add("A", 5.0, phase="liquid")

    def test_set_raises_if_not_registered(self) -> None:
        """set() on an unregistered species raises KeyError."""
        state = ReactorState()
        with pytest.raises(KeyError, match="Species 'A' not found"):
            state.set("A", 42.0, phase="liquid")

    def test_total_mass_empty(self) -> None:
        """total_mass on empty state returns 0."""
        state = ReactorState()
        assert state.total_mass() == 0.0
        assert state.total_mass(phase="liquid") == 0.0
        assert state.total_mass(phase="vapor") == 0.0
