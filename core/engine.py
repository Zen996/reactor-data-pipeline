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
        self._step_index: int = 0

    def step(self) -> None:
        """Execute exactly one timestep at the current clock."""
        t = self._step_index * self._dt
        if t >= self._duration:
            return
        self._current_time = t
        self._state.time = t
        for process in self._processes:
            process.execute(self._state, self._dt)
        self._recorder.record(self._state, t)
        self._step_index += 1

    def run_until(self, target_time: float) -> None:
        """Call step() repeatedly while step_time < target_time and
        step_time < duration."""
        target_steps = round(target_time / self._dt) if target_time > 0 else 0
        max_steps = round(self._duration / self._dt)
        while self._step_index < target_steps and self._step_index < max_steps:
            self.step()

    def run(self) -> None:
        """Advance the simulation from t=0 to t=duration."""
        self.run_until(self._duration)
        self._has_run = True
        self._recorder.finalize()

    def restore(self, state: HasTime, time: float) -> None:
        """Replace the live state and reset the clock to `time`.
        Caller is responsible for ensuring the state is valid at `time`.
        This is the only way to move time backward."""
        self._state = state
        self._current_time = time
        self._step_index = round(time / self._dt) + 1 if self._dt > 0 else 0

    @property
    def state(self) -> HasTime:
        """The current reactor state."""
        return self._state

    @property
    def current_time(self) -> float:
        return self._current_time
