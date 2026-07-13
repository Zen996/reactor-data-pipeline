"""Generic stoichiometric reactions — the second real Process.

All rates are computed from the **start-of-step** state, then all
deltas are accumulated and applied atomically so that reaction order in
the list does not affect the result within a single timestep.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.process import Process
from signals.base import Signal


@dataclass
class Reaction:
    """A single chemical transformation with its rate law.

    Parameters
    ----------
    reactants:
        Species name → stoichiometric coefficient (e.g. ``{"A": 2}``).
    products:
        Species name → stoichiometric coefficient (e.g. ``{"C": 3}``).
    rate_constant:
        Rate constant ``k``.  Can be a plain ``float`` or a
        :class:`~signals.base.Signal` evaluated at ``state.time`` each
        step (useful for time-varying / stochastic rate constants from
        Stage 9 onward).
    order:
        Per-species kinetic order.  If ``None`` (default), the
        stoichiometric coefficient of each reactant is used as its order
        (elementary-reaction assumption).  This is a simplification —
        real reaction orders are empirical.
    phase:
        Which phase the reaction occurs in.  Defaults to ``"liquid"``.
    """

    reactants: dict[str, int]
    products: dict[str, int]
    rate_constant: float | Signal
    order: dict[str, float] | None = None
    phase: str = "liquid"

    def __post_init__(self) -> None:
        if self.order is None:
            self.order = {s: float(c) for s, c in self.reactants.items()}


def _resolve_k(reaction: Reaction, t: float) -> float:
    k = reaction.rate_constant
    if isinstance(k, (int, float)):
        return float(k)
    return k.value(t)


def _compute_rate(
    state, reaction: Reaction, dt: float
) -> tuple[float, dict[str, float], dict[str, float]]:
    """Compute the reaction rate and the per-species deltas.

    Returns (clamped_extent_in_concentration, reactant_deltas, product_deltas).
    All deltas are in **absolute quantity** units (ready for
    ``state.add``).
    """
    vol = state.volume
    if vol <= 0:
        return 0.0, {}, {}

    # --- rate law ---
    rate = _resolve_k(reaction, state.time)
    for species, order in reaction.order.items():
        conc = state.concentration(species, phase=reaction.phase)
        rate *= conc ** order

    extent = rate * dt  # concentration units

    # --- clamp extent so no reactant goes negative ---
    for species, coeff in reaction.reactants.items():
        qty = state.get(species, phase=reaction.phase)
        max_extent_for_species = qty / (float(coeff) * vol) if coeff > 0 else float("inf")
        if max_extent_for_species < extent:
            extent = max_extent_for_species

    # --- per-species deltas (absolute quantity) ---
    reactant_deltas: dict[str, float] = {}
    for species, coeff in reaction.reactants.items():
        delta = float(coeff) * extent * vol
        reactant_deltas[species] = -delta

    product_deltas: dict[str, float] = {}
    for species, coeff in reaction.products.items():
        delta = float(coeff) * extent * vol
        product_deltas[species] = delta

    return extent, reactant_deltas, product_deltas


class ReactionProcess(Process):
    """Apply a list of independent :class:`Reaction` objects each step.

    All rates are computed from the start-of-step state.  Deltas are
    accumulated per species and applied atomically so that reaction order
    in the list does not change the result.
    """

    def __init__(self, reactions: list[Reaction]) -> None:
        self._reactions = list(reactions)

    def execute(self, state, dt: float) -> None:
        accumulated: dict[str, float] = {}

        for i, reaction in enumerate(self._reactions):
            extent, r_deltas, p_deltas = _compute_rate(state, reaction, dt)

            for species, delta in r_deltas.items():
                accumulated[species] = accumulated.get(species, 0.0) + delta
            for species, delta in p_deltas.items():
                accumulated[species] = accumulated.get(species, 0.0) + delta

            state.derived[f"reaction_rate_{i}"] = extent / dt if dt > 0 else 0.0

        for species, delta in accumulated.items():
            if species not in state.liquid and species not in state.vapor:
                state.register_species(species, phase="liquid", initial=0.0)
            state.add(species, delta)
