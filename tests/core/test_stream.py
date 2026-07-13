"""Tests for InputStream (Stage 4)."""

import pytest

from core.stream import InputStream
from signals.constant import Constant
from signals.step import Step
from signals.sinusoid import Sinusoid


class TestInputStream:
    """Acceptance criteria for Stage 4's InputStream."""

    def test_constant_flow_and_composition(self) -> None:
        """C1: Constant flow + Constant composition → flow_rate * concentration."""
        stream = InputStream(
            name="feed",
            flow_signal=Constant(5.0),
            composition={"A": Constant(2.0), "B": Constant(3.0)},
            phase="liquid",
        )
        for t in (0.0, 10.0, 100.0):
            assert stream.flow_rate(t) == 5.0
            inflow = stream.species_inflow(t)
            assert inflow["A"] == 10.0  # 5 * 2
            assert inflow["B"] == 15.0  # 5 * 3

    def test_step_flow_signal(self) -> None:
        """C2: Step flow signal returns correct before/after step time."""
        stream = InputStream(
            name="feed",
            flow_signal=Step(baseline=1.0, step_value=10.0, step_time=50.0),
            composition={"A": Constant(2.0)},
        )
        assert stream.flow_rate(0.0) == 1.0
        assert stream.flow_rate(49.999) == 1.0
        assert stream.flow_rate(50.0) == 10.0
        assert stream.flow_rate(100.0) == 10.0

        inflow_before = stream.species_inflow(0.0)
        assert inflow_before["A"] == 2.0  # 1 * 2
        inflow_after = stream.species_inflow(50.0)
        assert inflow_after["A"] == 20.0  # 10 * 2

    def test_inactive_returns_zero(self) -> None:
        """C3: active=False makes flow_rate and species_inflow return zero."""
        stream = InputStream(
            name="feed",
            flow_signal=Constant(10.0),
            composition={"A": Constant(5.0)},
            active=False,
        )
        assert stream.flow_rate(0.0) == 0.0
        assert stream.flow_rate(100.0) == 0.0
        inflow = stream.species_inflow(0.0)
        assert inflow["A"] == 0.0

    def test_set_active_toggle(self) -> None:
        """C3b: set_active(False) → zero; set_active(True) → nonzero again."""
        stream = InputStream(
            name="feed",
            flow_signal=Constant(10.0),
            composition={"A": Constant(5.0)},
            active=True,
        )
        assert stream.flow_rate(0.0) == 10.0

        stream.set_active(False)
        assert stream.flow_rate(0.0) == 0.0
        assert stream.species_inflow(0.0)["A"] == 0.0

        stream.set_active(True)
        assert stream.flow_rate(0.0) == 10.0
        assert stream.species_inflow(0.0)["A"] == 50.0

    def test_invalid_phase_raises(self) -> None:
        """C4: Invalid phase raises ValueError."""
        with pytest.raises(ValueError, match="Invalid phase"):
            InputStream(
                name="bad",
                flow_signal=Constant(1.0),
                composition={"A": Constant(1.0)},
                phase="solid",
            )

    def test_valid_phases(self) -> None:
        """Both valid phases work."""
        for phase in ("liquid", "vapor"):
            stream = InputStream(
                name="test",
                flow_signal=Constant(2.0),
                composition={"X": Constant(3.0)},
                phase=phase,
            )
            assert stream.phase == phase
            assert stream.flow_rate(0.0) == 2.0

    def test_independent_composition_signals(self) -> None:
        """C5: Signals in composition vary independently over time."""
        stream = InputStream(
            name="feed",
            flow_signal=Constant(10.0),
            composition={
                "A": Constant(2.0),
                "B": Sinusoid(amplitude=1.0, frequency=0.25, offset=3.0),
            },
        )
        # t=0: A=2, B=3+sin(0)=3 → A_in=20, B_in=30
        inflow0 = stream.species_inflow(0.0)
        assert inflow0["A"] == 20.0
        assert inflow0["B"] == pytest.approx(30.0)

        # t=1: B=3+sin(pi/2)=4 → B_in=40
        inflow1 = stream.species_inflow(1.0)
        assert inflow1["A"] == 20.0
        assert inflow1["B"] == pytest.approx(40.0)

        # t=2: B=3+sin(pi)=3 → B_in=30
        inflow2 = stream.species_inflow(2.0)
        assert inflow2["A"] == 20.0
        assert inflow2["B"] == pytest.approx(30.0)

    def test_species_inflow_no_mutation(self) -> None:
        """species_inflow returns a fresh dict each call."""
        stream = InputStream(
            name="feed",
            flow_signal=Constant(1.0),
            composition={"A": Constant(2.0)},
        )
        inflow1 = stream.species_inflow(0.0)
        inflow2 = stream.species_inflow(0.0)
        assert inflow1 is not inflow2
        assert inflow1 == inflow2

    def test_empty_composition(self) -> None:
        """A stream with no species is valid."""
        stream = InputStream(
            name="empty",
            flow_signal=Constant(5.0),
            composition={},
        )
        assert stream.flow_rate(0.0) == 5.0
        assert stream.species_inflow(0.0) == {}
