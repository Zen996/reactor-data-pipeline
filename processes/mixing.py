"""Perfect-mixing process — the first real Process.

Applies inflow streams, then proportional outlet removal, then volume
change.  This follows a semi-implicit / Euler convention often used for
CSTRs: **inflow is applied first**, then outlet removal is computed from
the updated bulk composition.
"""

from core.process import Process
from core.stream import InputStream
from signals.base import Signal


_VOLUME_EPSILON = 1e-12


class MixingProcess(Process):
    """Move material into and out of the reactor each timestep.

    Parameters
    ----------
    streams:
        Active feed lines.  Each stream's ``species_inflow()`` is
        evaluated at ``state.time``.
    outflow_rate:
        Volumetric outlet flow.  Can be:

        - ``None`` (default) — set equal to total inflow (constant-volume).
        - A ``float`` — fixed rate.
        - A ``Signal`` — evaluated at ``state.time`` each step.
    """

    def __init__(
        self,
        streams: list[InputStream],
        outflow_rate: Signal | float | None = None,
    ) -> None:
        self._streams = list(streams)
        self._outflow_rate = outflow_rate

    def execute(self, state, dt: float) -> None:
        t = state.time
        total_in = 0.0
        aggregated_inflows: dict[str, float] = {}

        # --- 1.  Apply inflow from every active stream ---
        for stream in self._streams:
            if not stream.active:
                continue

            total_in += stream.flow_rate(t)

            for species, rate in stream.species_inflow(t).items():
                aggregated_inflows[species] = (
                    aggregated_inflows.get(species, 0.0) + rate
                )

                # Auto-register new species
                try:
                    state.get(species, phase=stream.phase)
                except KeyError:
                    state.register_species(species, phase=stream.phase, initial=0.0)

                qty_added = rate * dt
                state.add(species, qty_added, phase=stream.phase)

        # --- 2.  Resolve outflow ---
        if self._outflow_rate is None:
            outflow = total_in
        elif isinstance(self._outflow_rate, (int, float)):
            outflow = float(self._outflow_rate)
        else:
            outflow = self._outflow_rate.value(t)

        # --- 3.  Proportional outlet removal (from updated bulk) ---
        for species in list(state.liquid.keys()):
            conc = state.liquid[species] / state.volume if state.volume > 0 else 0.0
            removed = outflow * conc * dt
            state.add(species, -removed, phase="liquid")

        # --- 4.  Update volume ---
        delta_v = (total_in - outflow) * dt
        new_volume = state.volume + delta_v
        if new_volume <= 0.0:
            new_volume = _VOLUME_EPSILON
        state.volume = new_volume

        # --- 5.  Record per-stream detail (Stage 13 GUI) ---
        for stream in self._streams:
            name = stream.name
            state.derived[f"stream.{name}.flow_rate"] = stream.flow_rate(t)
            inp = stream.species_inflow(t)
            for species, rate in inp.items():
                state.derived[f"stream.{name}.inflow.{species}"] = rate

        for species in list(state.liquid.keys()):
            conc = state.liquid[species] / state.volume if state.volume > 0 else 0.0
            state.derived[f"outlet.{species}"] = outflow * conc

        state.inflows = aggregated_inflows
        state.outflow_rate = outflow
