"""Centralised, reproducible randomness for the entire simulation.

Usage::

    rm = RandomManager(seed=42)
    gen_a = rm.spawn("sensor.temperature")
    gen_b = rm.spawn("feed.disturbance_1")

Each call to ``spawn()`` advances an internal counter within the
:class:`numpy.random.SeedSequence`, so every stream is independent and
fully reproducible when the same top-level seed and the same spawn order
are used.

The *name* argument is logged for traceability but does **not** affect
the generated stream — only the spawn order matters.
"""

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.random import Generator

logger = logging.getLogger(__name__)


class RandomManager:
    """Owns a :class:`numpy.random.SeedSequence` and spawns independent
    :class:`~numpy.random.Generator` instances on demand.

    Parameters
    ----------
    seed:
        Top-level seed.  Pass ``None`` to use OS entropy (logged as a
        warning since this makes the run non-reproducible).
    """

    def __init__(self, seed: int | None) -> None:
        if seed is None:
            logger.warning(
                "RandomManager created with seed=None — the run will NOT "
                "be reproducible."
            )
        self._base_seq = np.random.SeedSequence(seed)
        self._spawn_count: int = 0

    def spawn(self, name: str = "") -> "Generator":
        """Return a new independent :class:`~numpy.random.Generator`.

        Each call advances the internal spawn counter, so repeated calls
        produce different (still reproducible) streams.  The *name* is
        logged for debugging but does not affect the generated stream.
        """
        child_seq = self._base_seq.spawn(1)[0]
        gen = np.random.default_rng(child_seq)
        self._spawn_count += 1
        logger.debug("RandomManager.spawn #%d: %s", self._spawn_count, name)
        return gen

    @property
    def spawn_count(self) -> int:
        return self._spawn_count
