import pytest

from signals.ramp import Ramp


class TestRamp:
    def test_before_start(self) -> None:
        r = Ramp(start_value=5.0, slope=2.0, start_time=3.0)
        assert r.value(0.0) == 5.0
        assert r.value(2.999) == 5.0

    def test_linear_after_start(self) -> None:
        r = Ramp(start_value=5.0, slope=2.0, start_time=3.0)
        assert r.value(3.0) == 5.0
        assert r.value(4.0) == 7.0  # 5 + 2*1
        assert r.value(8.0) == 15.0  # 5 + 2*5

    def test_saturates_at_max(self) -> None:
        r = Ramp(start_value=0.0, slope=1.0, start_time=0.0, max_value=5.0)
        assert r.value(3.0) == 3.0
        assert r.value(5.0) == 5.0
        assert r.value(10.0) == 5.0  # clamped

    def test_saturates_at_min(self) -> None:
        r = Ramp(start_value=10.0, slope=-2.0, start_time=0.0, min_value=0.0)
        assert r.value(3.0) == 4.0
        assert r.value(5.0) == 0.0  # 10 + (-2)*5 = 0
        assert r.value(10.0) == 0.0

    def test_both_clamps(self) -> None:
        r = Ramp(start_value=0.0, slope=-1.0, start_time=0.0,
                 min_value=-5.0, max_value=5.0)
        # t=-10 is before start_time → returns start_value=0.0 (no clamp needed)
        assert r.value(-10.0) == 0.0
        # t=10: 0 + (-1)*10 = -10, clamped to min=-5
        assert r.value(10.0) == -5.0
        # Also verify upper clamp: at t=-10 (before start) max clamp isn't applied
        # but at t=-10 with a positive slope it would be:
        r2 = Ramp(start_value=0.0, slope=1.0, start_time=0.0,
                  min_value=-5.0, max_value=5.0)
        # t=10: 0 + 1*10 = 10, clamped to max=5
        assert r2.value(10.0) == 5.0

    def test_default_start_time(self) -> None:
        r = Ramp(start_value=10.0, slope=3.0)
        assert r.value(0.0) == 10.0
        assert r.value(2.0) == 16.0
