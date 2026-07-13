import pytest

from signals.constant import Constant


class TestConstant:
    def test_constant_value(self) -> None:
        s = Constant(42.0)
        for t in (-1.0, 0.0, 1.0, 100.0):
            assert s.value(t) == 42.0

    def test_zero(self) -> None:
        s = Constant(0.0)
        assert s.value(0.0) == 0.0
        assert s.value(1e6) == 0.0

    def test_negative(self) -> None:
        s = Constant(-3.5)
        assert s.value(10.0) == -3.5
