"""Tests for SimulationEngine (Stage 1)."""

from dataclasses import dataclass, field
from typing import Any

from core.process import Process, Recorder


# ── Helpers ────────────────────────────────────────────────────────────

@dataclass
class DummyState:
    time: float = 0.0
    counter: int = 0
    log: list[str] = field(default_factory=list)


class CounterProcess(Process):
    """Increments `state.counter` by 1 each step."""

    def execute(self, state: DummyState, dt: float) -> None:
        state.counter += 1


class RecorderSpy(Recorder):
    """In-memory recorder that records (sim_time, counter) tuples."""

    def __init__(self) -> None:
        self.records: list[tuple[float, Any]] = []
        self.finalize_calls: int = 0

    def record(self, state: DummyState, sim_time: float) -> None:
        self.records.append((sim_time, state.counter))

    def finalize(self) -> None:
        self.finalize_calls += 1


class NamedProcess(Process):
    """Appends its name to `state.log` on each execution."""

    def __init__(self, name: str) -> None:
        self._name = name

    def execute(self, state: DummyState, dt: float) -> None:
        state.log.append(self._name)


# ── Tests ──────────────────────────────────────────────────────────────


class TestSimulationEngine:
    """Acceptance criteria for Stage 1's SimulationEngine."""

    def test_counter_process_runs_exact_steps(self) -> None:
        """C1: dummy Process increments counter — duration=10, dt=1 → counter=10."""
        from core.engine import SimulationEngine

        state = DummyState()
        recorder = RecorderSpy()
        engine = SimulationEngine(
            initial_state=state,
            processes=[CounterProcess()],
            recorder=recorder,
            dt=1.0,
            duration=10.0,
        )
        engine.run()

        assert state.counter == 10

    def test_recorded_times_and_values(self) -> None:
        """C2: recorded (sim_time, counter) tuples match expected convention.

        Records happen *after* processes run for the step, using the
        simulation time at the *start* of that step.  With counter
        incrementing by 1 per step, after step i (t=i):
            state.counter = i+1
        So records should be [(0, 1), (1, 2), ..., (9, 10)].
        """
        from core.engine import SimulationEngine

        state = DummyState()
        recorder = RecorderSpy()
        engine = SimulationEngine(
            initial_state=state,
            processes=[CounterProcess()],
            recorder=recorder,
            dt=1.0,
            duration=10.0,
        )
        engine.run()

        assert len(recorder.records) == 10
        for i, (sim_time, counter) in enumerate(recorder.records):
            assert sim_time == i * 1.0
            assert counter == i + 1

    def test_process_execution_order(self) -> None:
        """C3: multiple processes execute in the order passed."""
        from core.engine import SimulationEngine

        state = DummyState()
        recorder = RecorderSpy()
        processes = [NamedProcess("A"), NamedProcess("B"), NamedProcess("C")]
        engine = SimulationEngine(
            initial_state=state,
            processes=processes,
            recorder=recorder,
            dt=1.0,
            duration=1.0,
        )
        engine.run()

        assert state.log == ["A", "B", "C"]

    def test_non_positive_dt_raises(self) -> None:
        """C4a: dt <= 0 raises ValueError."""
        from core.engine import SimulationEngine

        state = DummyState()
        recorder = RecorderSpy()

        for bad_dt in (0.0, -0.1, -1.0):
            try:
                SimulationEngine(
                    initial_state=state,
                    processes=[CounterProcess()],
                    recorder=recorder,
                    dt=bad_dt,
                    duration=10.0,
                )
                assert False, f"Expected ValueError for dt={bad_dt}"
            except ValueError:
                pass

    def test_non_positive_duration_raises(self) -> None:
        """C4b: duration <= 0 raises ValueError."""
        from core.engine import SimulationEngine

        state = DummyState()
        recorder = RecorderSpy()

        for bad_dur in (0.0, -0.1, -5.0):
            try:
                SimulationEngine(
                    initial_state=state,
                    processes=[CounterProcess()],
                    recorder=recorder,
                    dt=1.0,
                    duration=bad_dur,
                )
                assert False, f"Expected ValueError for duration={bad_dur}"
            except ValueError:
                pass

    def test_finalize_called_exactly_once(self) -> None:
        """C5: recorder.finalize() is called once after last step, not per step."""
        from core.engine import SimulationEngine

        state = DummyState()
        recorder = RecorderSpy()
        engine = SimulationEngine(
            initial_state=state,
            processes=[CounterProcess()],
            recorder=recorder,
            dt=1.0,
            duration=10.0,
        )
        engine.run()

        assert recorder.finalize_calls == 1

    def test_empty_processes_list(self) -> None:
        """C6: empty processes runs without error, still records each step."""
        from core.engine import SimulationEngine

        state = DummyState()
        recorder = RecorderSpy()
        engine = SimulationEngine(
            initial_state=state,
            processes=[],
            recorder=recorder,
            dt=1.0,
            duration=5.0,
        )
        engine.run()

        assert len(recorder.records) == 5

    def test_state_time_set_each_step(self) -> None:
        """State.time is set by engine before processes run each step."""
        from core.engine import SimulationEngine

        class TimeChecker(Process):
            def execute(self, state: DummyState, dt: float) -> None:
                state.counter += 1
                state.log.append(f"t={state.time}")

        state = DummyState()
        recorder = RecorderSpy()
        engine = SimulationEngine(
            initial_state=state,
            processes=[TimeChecker()],
            recorder=recorder,
            dt=1.0,
            duration=3.0,
        )
        engine.run()

        assert state.log == ["t=0.0", "t=1.0", "t=2.0"]

    def test_current_time_and_state_after_run(self) -> None:
        """Properties expose correct current_time and state after run."""
        from core.engine import SimulationEngine

        state = DummyState()
        recorder = RecorderSpy()
        engine = SimulationEngine(
            initial_state=state,
            processes=[CounterProcess()],
            recorder=recorder,
            dt=1.0,
            duration=10.0,
        )
        engine.run()

        assert engine.current_time == 9.0
        assert engine.state is state
