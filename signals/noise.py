import numpy as np

from signals.base import Signal


class GaussianNoise(Signal):
    """Normally-distributed noise with configurable mean and standard
    deviation.

    Each call to ``value(t)`` advances the internal RNG, so repeated
    calls with the same ``t`` produce different results (unlike
    deterministic signals). Accepts an optional ``seed`` for reproducible
    output.
    """

    def __init__(self, mean: float = 0.0, std: float = 1.0, seed: int | None = None) -> None:
        self._mean = mean
        self._std = std
        self._rng = np.random.default_rng(seed)

    def value(self, t: float) -> float:
        return float(self._rng.normal(self._mean, self._std))


class UniformNoise(Signal):
    """Uniformly-distributed noise in ``[low, high]``.

    Same caveat about RNG state and reproducibility as
    :class:`GaussianNoise`.
    """

    def __init__(self, low: float = 0.0, high: float = 1.0, seed: int | None = None) -> None:
        self._low = low
        self._high = high
        self._rng = np.random.default_rng(seed)

    def value(self, t: float) -> float:
        return float(self._rng.uniform(self._low, self._high))
