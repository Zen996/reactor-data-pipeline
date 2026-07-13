"""Liquid / vapour phase equilibrium for individual species.

Net transfer follows::

    net = evaporation_coeff * conc(liquid) - condensation_coeff * conc(vapor)

Positive ``net`` means liquid → vapour.  The process auto-registers
species in the target phase if they do not yet exist there.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.process import Process


@dataclass
class PhaseEquilibrium:
    """Equilibrium pair for a single species across two phases.

    Parameters
    ----------
    species:
        The species name (must exist in at least one phase).
    evaporation_coeff:
        Rate coefficient for liquid → vapour transfer (>= 0).
    condensation_coeff:
        Rate coefficient for vapour → liquid transfer (>= 0).
    """

    species: str
    evaporation_coeff: float
    condensation_coeff: float


class EquilibriumProcess(Process):
    """Apply a list of phase-equilibrium pairs each step."""

    def __init__(self, pairs: list[PhaseEquilibrium]) -> None:
        self._pairs = list(pairs)

    def execute(self, state, dt: float) -> None:
        vol = state.volume
        if vol <= 0:
            return

        for pair in self._pairs:
            # --- get current concentrations ---
            try:
                liq_conc = state.concentration(pair.species, phase="liquid")
            except KeyError:
                liq_conc = 0.0
                state.register_species(pair.species, phase="liquid", initial=0.0)

            try:
                vap_conc = state.concentration(pair.species, phase="vapor")
            except KeyError:
                vap_conc = 0.0
                state.register_species(pair.species, phase="vapor", initial=0.0)

            # --- net transfer (concentration units) ---
            net = pair.evaporation_coeff * liq_conc - pair.condensation_coeff * vap_conc
            extent = net * dt  # concentration, positive = liquid -> vapour

            # --- clamp so neither phase goes negative ---
            liq_qty = state.get(pair.species, phase="liquid")
            vap_qty = state.get(pair.species, phase="vapor")

            if extent > 0:
                max_extent = liq_qty / vol if vol > 0 else 0.0
                if extent > max_extent:
                    extent = max_extent
            elif extent < 0:
                min_extent = -vap_qty / vol if vol > 0 else 0.0  # negative
                if extent < min_extent:
                    extent = min_extent

            delta_qty = extent * vol
            state.add(pair.species, -delta_qty, phase="liquid")
            state.add(pair.species, delta_qty, phase="vapor")

            state.derived[f"equilibrium_net_{pair.species}"] = net
