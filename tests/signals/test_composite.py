import pytest

from signals.constant import Constant
from signals.step import Step
from signals.sinusoid import Sinusoid
from signals.composite import CompositeSignal


class TestCompositeSignal:
    def test_dispatch_to_correct_segment(self) -> None:
        """Reproduce the exact brief example."""
        segments = [
            (0.0, 100.0, Constant(5.0)),
            (100.0, 250.0, Step(baseline=0.0, step_value=10.0, step_time=100.0)),
            (250.0, 500.0, Sinusoid(amplitude=2.0, frequency=0.01, offset=3.0)),
        ]
        c = CompositeSignal(segments)

        assert c.value(0.0) == 5.0
        assert c.value(50.0) == 5.0
        assert c.value(99.999) == 5.0

        assert c.value(100.0) == 10.0
        assert c.value(200.0) == 10.0
        assert c.value(249.999) == 10.0

        # t=250: sin(2*pi*0.01*250) = sin(5*pi) = 0 => 3
        assert c.value(250.0) == pytest.approx(3.0)
        # t=275: sin(2*pi*0.01*275) = sin(5.5*pi) = sin(1.5*pi) = -1 => 3-2=1
        assert c.value(275.0) == pytest.approx(1.0)

    def test_value_at_gap_raises(self) -> None:
        segments = [
            (0.0, 10.0, Constant(1.0)),
            (20.0, 30.0, Constant(2.0)),
        ]
        c = CompositeSignal(segments)
        with pytest.raises(ValueError, match="No active segment"):
            c.value(15.0)
        with pytest.raises(ValueError, match="No active segment"):
            c.value(35.0)

    def test_at_segment_boundary(self) -> None:
        """Left boundary inclusive, right exclusive."""
        segments = [
            (0.0, 10.0, Constant(1.0)),
            (10.0, 20.0, Constant(2.0)),
        ]
        c = CompositeSignal(segments)
        assert c.value(0.0) == 1.0
        assert c.value(9.999) == 1.0
        assert c.value(10.0) == 2.0  # right boundary of [0,10) is start of next
        assert c.value(19.999) == 2.0

    def test_overlapping_segments_raises(self) -> None:
        with pytest.raises(ValueError, match="overlap"):
            CompositeSignal([
                (0.0, 10.0, Constant(1.0)),
                (5.0, 15.0, Constant(2.0)),
            ])

    def test_empty_segments_raises(self) -> None:
        with pytest.raises(ValueError, match="At least one segment"):
            CompositeSignal([])

    def test_segments_sorted_automatically(self) -> None:
        c = CompositeSignal([
            (10.0, 20.0, Constant(2.0)),
            (0.0, 10.0, Constant(1.0)),
        ])
        assert c.value(5.0) == 1.0
        assert c.value(15.0) == 2.0
