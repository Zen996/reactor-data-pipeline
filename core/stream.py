"""InputStream abstraction — one feed line into the reactor.

This module lives in ``core/`` because both ``config/`` (Stage 11) and
``processes/mixing.py`` (Stage 5) need it, and it is a data/behaviour
abstraction, not a ``Process``.  See the note in ``00_overview.md``.
"""

from signals.base import Signal


_VALID_PHASES = ("liquid", "vapor")


class InputStream:
    """A single feed line into the reactor.

    Driven entirely by :class:`~signals.base.Signal` objects — one for
    volumetric flow rate, one per species for feed concentration.  When
    the stream is *inactive* (``active=False``), both ``flow_rate()`` and
    ``species_inflow()`` return ``0.0`` regardless of the underlying
    signals, so that Stage 8 manipulations can toggle streams on/off
    without recreating them.

    Concentrations are in the same (arbitrary) units as
    :class:`~core.state.ReactorState`; they do **not** need to sum to 1.0
    or any other value.

    .. note::

        ``InputStream`` has **no** reference to ``ReactorState`` — it is
        a pure, independently testable unit that only knows about signals
        and time.
    """

    def __init__(
        self,
        name: str,
        flow_signal: Signal,
        composition: dict[str, Signal],
        phase: str = "liquid",
        active: bool = True,
    ) -> None:
        if phase not in _VALID_PHASES:
            raise ValueError(
                f"Invalid phase {phase!r}; must be one of {_VALID_PHASES}"
            )
        self.name = name
        self._flow_signal = flow_signal
        self._composition = composition
        self._phase = phase
        self._active = active

    @property
    def phase(self) -> str:
        return self._phase

    def flow_rate(self, t: float) -> float:
        """Volumetric flow rate at simulation time ``t``.

        Returns ``0.0`` when the stream is inactive.
        """
        if not self._active:
            return 0.0
        return self._flow_signal.value(t)

    def species_inflow(self, t: float) -> dict[str, float]:
        """Per-species inflow rate at simulation time ``t``.

        Each entry is ``concentration_signal.value(t) * flow_rate(t)``.
        Returns an empty dict when the stream is inactive (flow is zero).
        """
        flow = self.flow_rate(t)
        if flow == 0.0:
            return {species: 0.0 for species in self._composition}
        return {
            species: conc_signal.value(t) * flow
            for species, conc_signal in self._composition.items()
        }

    def set_active(self, active: bool) -> None:
        """Enable or disable this stream without recreating it."""
        self._active = active

    @property
    def active(self) -> bool:
        return self._active
