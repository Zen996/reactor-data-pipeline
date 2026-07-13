import numpy as np

from signals.base import Signal


class GaussianNoise(Signal):
    """Normally-distributed noise with configurable mean and standard
    deviation.

    Prefer passing a ``generator`` (from :class:`RandomManager.spawn()
    <core.random_manager.RandomManager>`) for reproducible, project-wide
    randomness.  Falls back to a locally-seeded generator built from
    ``seed`` for standalone use.

    Each call to ``value(t)`` advances the RNG, so repeated calls with
    the same ``t`` produce different results (unlike deterministic
    signals).
    """

    def __init__(
        self,
        mean: float = 0.0,
        std: float = 1.0,
        generator: np.random.Generator | None = None,
        seed: int | None = None,
    ) -> None:
        self._mean = mean
        self._std = std
        if generator is not None:
            self._rng = generator
        else:
            self._rng = np.random.default_rng(seed)

    def value(self, t: float) -> float:
        return float(self._rng.normal(self._mean, self._std))


class UniformNoise(Signal):
    """Uniformly-distributed noise in ``[low, high]``.

    Same generator / seed fallback pattern as :class:`GaussianNoise`.
    """

    def __init__(
        self,
        low: float = 0.0,
        high: float = 1.0,
        generator: np.random.Generator | None = None,
        seed: int | None = None,
    ) -> None:
        self._low = low
        self._high = high
        if generator is not None:
            self._rng = generator
        else:
            self._rng = np.random.default_rng(seed)

    def value(self, t: float) -> float:
        return float(self._rng.uniform(self._low, self._high))
