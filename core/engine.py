from typing import Protocol

from core.process import Process, Recorder


class HasTime(Protocol):
    time: float


class SimulationEngine:
    """Fixed-timestep simulation loop that executes an ordered list of
    Process objects each step.

    The engine is the sole owner of the simulation clock. It sets
    ``state.time`` before running processes for each step so that every
    process sees a consistent time. After all steps complete,
    ``recorder.finalize()`` is called exactly once.

    Recording happens *after* processes execute for the step, using the
    simulation time at the *start* of that step.
    """

    def __init__(
        self,
        initial_state: HasTime,
        processes: list[Process],
        recorder: Recorder,
        dt: float,
        duration: float,
    ) -> None:
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")
        if duration <= 0:
            raise ValueError(f"duration must be positive, got {duration}")

        self._state = initial_state
        self._processes = list(processes)
        self._recorder = recorder
        self._dt = dt
        self._duration = duration
        self._current_time: float = 0.0
        self._has_run: bool = False

    def run(self) -> None:
        """Advance the simulation from t=0 to t=duration in steps of dt."""
        n_steps = round(self._duration / self._dt)

        for i in range(n_steps):
            t = i * self._dt
            self._current_time = t

            self._state.time = t

            for process in self._processes:
                process.execute(self._state, self._dt)

            self._recorder.record(self._state, t)

        self._has_run = True
        self._recorder.finalize()

    @property
    def state(self) -> HasTime:
        """The current (or final, after run()) reactor state."""
        return self._state

    @property
    def current_time(self) -> float:
        return self._current_time
