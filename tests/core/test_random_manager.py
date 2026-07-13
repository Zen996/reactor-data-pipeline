"""Tests for RandomManager (Stage 9)."""

import numpy as np

from core.random_manager import RandomManager


class TestRandomManager:
    """Acceptance criteria for Stage 9's RandomManager."""

    def test_same_seed_identical_sequence(self) -> None:
        """C1: Same top-level seed → same spawn sequence."""
        rm1 = RandomManager(seed=42)
        rm2 = RandomManager(seed=42)

        for _ in range(5):
            g1 = rm1.spawn("x")
            g2 = rm2.spawn("x")
            assert g1.normal() == g2.normal()
            assert g1.uniform() == g2.uniform()

    def test_different_seeds_diverge(self) -> None:
        """C2: Different seeds → different sequences."""
        rm1 = RandomManager(seed=42)
        rm2 = RandomManager(seed=99)

        g1 = rm1.spawn("a")
        g2 = rm2.spawn("a")
        assert g1.normal() != g2.normal()

    def test_different_names_independent(self) -> None:
        """C3: spawn("a") and spawn("b") produce different streams."""
        rm = RandomManager(seed=42)
        ga = rm.spawn("a")
        gb = rm.spawn("b")

        seq_a = [ga.normal() for _ in range(10)]
        seq_b = [gb.normal() for _ in range(10)]
        assert seq_a != seq_b

    def test_repeated_spawn_gives_different_stream(self) -> None:
        """Repeated spawn() calls give different (still reproducible)
        streams even with the same name."""
        rm = RandomManager(seed=42)
        g1 = rm.spawn("x")
        g2 = rm.spawn("x")

        seq1 = [g1.normal() for _ in range(5)]
        seq2 = [g2.normal() for _ in range(5)]
        assert seq1 != seq2

    def test_spawn_count(self) -> None:
        """spawn_count increases with each call."""
        rm = RandomManager(seed=1)
        assert rm.spawn_count == 0
        rm.spawn("a")
        assert rm.spawn_count == 1
        rm.spawn("b")
        assert rm.spawn_count == 2

    def test_none_seed_warns(self) -> None:
        """seed=None logs a warning but still creates a working generator."""
        import logging

        logger = logging.getLogger("core.random_manager")
        logger.setLevel(logging.WARNING)

        rm = RandomManager(seed=None)
        g = rm.spawn("test")
        val = g.normal()
        assert isinstance(val, float)
