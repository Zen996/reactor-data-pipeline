import pytest

from signals.noise import GaussianNoise, UniformNoise


class TestGaussianNoise:
    def test_same_seed_identical_sequence(self) -> None:
        n1 = GaussianNoise(mean=0.0, std=1.0, seed=42)
        n2 = GaussianNoise(mean=0.0, std=1.0, seed=42)
        seq1 = [n1.value(i) for i in range(10)]
        seq2 = [n2.value(i) for i in range(10)]
        assert seq1 == seq2

    def test_different_seeds_different_sequences(self) -> None:
        n1 = GaussianNoise(mean=0.0, std=1.0, seed=42)
        n2 = GaussianNoise(mean=0.0, std=1.0, seed=99)
        assert n1.value(0) != n2.value(0)

    def test_default_seed_is_random(self) -> None:
        """No seed: each instance should produce a different first value
        (extremely unlikely to collide)."""
        n1 = GaussianNoise(mean=0.0, std=1.0)
        n2 = GaussianNoise(mean=0.0, std=1.0)
        # Extremely unlikely to be equal
        assert n1.value(0) != n2.value(0) or n1.value(1) != n2.value(1)


class TestUniformNoise:
    def test_same_seed_identical_sequence(self) -> None:
        u1 = UniformNoise(low=0.0, high=1.0, seed=42)
        u2 = UniformNoise(low=0.0, high=1.0, seed=42)
        assert [u1.value(i) for i in range(10)] == [u2.value(i) for i in range(10)]

    def test_values_in_range(self) -> None:
        u = UniformNoise(low=-5.0, high=10.0, seed=42)
        for i in range(100):
            v = u.value(float(i))
            assert -5.0 <= v <= 10.0

    def test_low_equals_high(self) -> None:
        u = UniformNoise(low=3.0, high=3.0, seed=42)
        assert u.value(0.0) == 3.0
