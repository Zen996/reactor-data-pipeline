import math

import pytest

from signals.sinusoid import Sinusoid, SquareWave, TriangleWave


class TestSinusoid:
    def test_known_values(self) -> None:
        s = Sinusoid(amplitude=2.0, frequency=0.25, phase=0.0, offset=1.0)
        # t=0: 1 + 2*sin(0) = 1
        assert s.value(0.0) == pytest.approx(1.0)
        # t=1 (quarter period): 1 + 2*sin(pi/2) = 3
        assert s.value(1.0) == pytest.approx(3.0)
        # t=2 (half period): 1 + 2*sin(pi) = 1
        assert s.value(2.0) == pytest.approx(1.0)
        # t=3 (three quarters): 1 + 2*sin(3pi/2) = -1
        assert s.value(3.0) == pytest.approx(-1.0)
        # t=4 (full period): back to 1
        assert s.value(4.0) == pytest.approx(1.0)

    def test_with_phase(self) -> None:
        s = Sinusoid(amplitude=1.0, frequency=1.0, phase=math.pi / 2)
        # sin(t + pi/2) = cos(t), so at t=0 => 1
        assert s.value(0.0) == pytest.approx(1.0)

    def test_rectified(self) -> None:
        s = Sinusoid(amplitude=2.0, frequency=0.25, phase=0.0,
                     offset=0.0, rectified=True)
        # Never below 0
        for t in range(0, 100):
            assert s.value(t / 10) >= 0.0

    def test_rectified_quarter_period(self) -> None:
        s = Sinusoid(amplitude=2.0, frequency=0.25, phase=0.0,
                     offset=0.0, rectified=True)
        # t=1: abs(sin(pi/2)) = 1 => 1*2 = 2
        assert s.value(1.0) == pytest.approx(2.0)
        # t=3: abs(sin(3pi/2)) = abs(-1) = 1 => 2
        assert s.value(3.0) == pytest.approx(2.0)


class TestSquareWave:
    def test_default_duty_cycle(self) -> None:
        w = SquareWave(amplitude=1.0, frequency=1.0)
        # period=1, duty=0.5 => high for [0, 0.5), low for [0.5, 1)
        assert w.value(0.0) == pytest.approx(1.0)
        assert w.value(0.25) == pytest.approx(1.0)
        assert w.value(0.5) == pytest.approx(-1.0)
        assert w.value(0.75) == pytest.approx(-1.0)

    def test_custom_duty_cycle(self) -> None:
        w = SquareWave(amplitude=2.0, frequency=0.5, duty_cycle=0.25)
        # period=2, high for [0, 0.5), low for [0.5, 2)
        assert w.value(0.0) == pytest.approx(2.0)
        assert w.value(0.49) == pytest.approx(2.0)
        assert w.value(0.5) == pytest.approx(-2.0)
        assert w.value(1.5) == pytest.approx(-2.0)
        # next period
        assert w.value(2.0) == pytest.approx(2.0)

    def test_offset(self) -> None:
        w = SquareWave(amplitude=1.0, frequency=1.0, offset=3.0)
        assert w.value(0.0) == pytest.approx(4.0)  # 3+1
        assert w.value(0.6) == pytest.approx(2.0)  # 3-1


class TestTriangleWave:
    def test_shape(self) -> None:
        t = TriangleWave(amplitude=2.0, frequency=1.0)
        # period=1, half_period=0.5
        # t=0: -2
        assert t.value(0.0) == pytest.approx(-2.0)
        # t=0.25: -2 + 4*0.25/0.5 = -2 + 2 = 0 ... actually:
        # fraction = 0.25/0.5 = 0.5 => -2 + 2*0.5*2 = 0
        assert t.value(0.25) == pytest.approx(0.0)
        # t=0.5: +2
        assert t.value(0.5) == pytest.approx(2.0)
        # t=0.75: fraction = 0.25/0.5 = 0.5 => 2 - 4*0.5 = 0
        assert t.value(0.75) == pytest.approx(0.0)
        # t=1.0: back to -2
        assert t.value(1.0) == pytest.approx(-2.0)

    def test_offset(self) -> None:
        t = TriangleWave(amplitude=1.0, frequency=0.5, offset=5.0)
        # period=2, t=0 => 5-1=4, t=1 => 5+1=6
        assert t.value(0.0) == pytest.approx(4.0)
        assert t.value(1.0) == pytest.approx(6.0)
