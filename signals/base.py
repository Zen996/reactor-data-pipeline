from abc import ABC, abstractmethod


class Signal(ABC):
    """A time-dependent value generator.

    All signals are stateless with respect to simulation progress —
    calling ``value(t)`` twice with the same ``t`` returns the same
    result — except noise signals, which necessarily hold mutable RNG
    state (see :mod:`signals.noise`).

    Frequencies are in Hz (cycles per second of simulation time),
    consistent with the ``dt`` / ``duration`` conventions used elsewhere
    in the project.
    """

    @abstractmethod
    def value(self, t: float) -> float:
        """Return the signal value at simulation time ``t``."""
        ...
