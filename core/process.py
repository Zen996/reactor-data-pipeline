from abc import ABC, abstractmethod


class Process(ABC):
    """A single transformation applied to reactor state each timestep."""

    @abstractmethod
    def execute(self, state, dt: float) -> None:
        """Mutate `state` in place to reflect the passage of `dt` seconds."""
        ...


class Recorder(ABC):
    """Minimal recorder contract. Fully implemented in Stage 10."""

    @abstractmethod
    def record(self, state, sim_time: float) -> None:
        ...

    def finalize(self) -> None:
        """Optional hook called once after the run completes. No-op by default."""
        return None
