import pytest

from signals.step import Step


class TestStep:
    def test_before_step(self) -> None:
        s = Step(baseline=0.0, step_value=10.0, step_time=5.0)
        assert s.value(0.0) == 0.0
        assert s.value(4.999) == 0.0

    def test_at_and_after_step(self) -> None:
        s = Step(baseline=0.0, step_value=10.0, step_time=5.0)
        assert s.value(5.0) == 10.0
        assert s.value(5.001) == 10.0
        assert s.value(100.0) == 10.0

    def test_step_at_zero(self) -> None:
        s = Step(baseline=1.0, step_value=2.0, step_time=0.0)
        assert s.value(-1.0) == 1.0
        assert s.value(0.0) == 2.0

    def test_negative_step_time(self) -> None:
        s = Step(baseline=0.0, step_value=5.0, step_time=-10.0)
        assert s.value(-11.0) == 0.0
        assert s.value(-10.0) == 5.0
