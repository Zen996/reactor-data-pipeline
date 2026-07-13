"""First-order decay — reduces a species and optionally produces others.

All rates use the start-of-step concentration and deltas are accumulated
atomically, matching the order-independence convention of
:class:`~processes.reaction.ReactionProcess`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.process import Process


@dataclass
class DecayRule:
    """First-order decay rule for one species.

    Parameters
    ----------
    species:
        The species that decays.
    rate_constant:
        First-order rate constant ``k``.
    phase:
        Phase to operate in (``"liquid"`` or ``"vapor"``).
    products:
        Optional stoichiometric products, e.g. ``{"A": 2}`` means
        each decay event produces 2 units of A.  Empty dict means the
        species is a pure sink (mass disappears).
    """

    species: str
    rate_constant: float
    phase: str = "liquid"
    products: dict[str, int] = field(default_factory=dict)


class DecayProcess(Process):
    """Apply a list of first-order decay rules each step."""

    def __init__(self, rules: list[DecayRule]) -> None:
        self._rules = list(rules)

    def execute(self, state, dt: float) -> None:
        vol = state.volume
        if vol <= 0:
            return

        accumulated: dict[str, float] = {}

        for i, rule in enumerate(self._rules):
            conc = state.concentration(rule.species, phase=rule.phase)
            rate = rule.rate_constant * conc
            extent = rate * dt  # concentration units

            state.derived[f"decay_rate_{rule.species}"] = rate

            # clamp so decaying species doesn't go negative
            qty = state.get(rule.species, phase=rule.phase)
            max_extent = qty / vol if vol > 0 else 0.0
            if extent > max_extent:
                extent = max_extent

            # decay: remove from parent species
            delta = -extent * vol
            accumulated[rule.species] = accumulated.get(rule.species, 0.0) + delta

            # products
            for prod_species, coeff in rule.products.items():
                prod_delta = float(coeff) * extent * vol
                accumulated[prod_species] = (
                    accumulated.get(prod_species, 0.0) + prod_delta
                )

        for species, delta in accumulated.items():
            if species not in state.liquid and species not in state.vapor:
                state.register_species(species, phase="liquid", initial=0.0)
            state.add(species, delta)
