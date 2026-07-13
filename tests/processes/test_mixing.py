"""Tests for MixingProcess (Stage 5)."""

import pytest

from core.state import ReactorState
from core.stream import InputStream
from processes.mixing import MixingProcess
from signals.constant import Constant
from signals.step import Step


class TestMixingProcess:
    """Acceptance criteria for Stage 5's MixingProcess."""

    def test_single_stream_constant_volume(self) -> None:
        """C1: Single constant stream, default outflow = total_in.

        After one step (dt=1, flow=10, conc=2):
          - volume unchanged (10 in, 10 out)
          - A increases by (10*2*1) - (10 * post_inflow_A / V * 1)
        """
        state = ReactorState(volume=100.0, time=0.0)
        state.register_species("A", phase="liquid", initial=50.0)

        stream = InputStream(
            name="feed",
            flow_signal=Constant(10.0),
            composition={"A": Constant(2.0)},
        )
        process = MixingProcess(streams=[stream])

        process.execute(state, dt=1.0)

        # Volume unchanged
        assert state.volume == pytest.approx(100.0)

        # Inflow first: 50 + 20 = 70
        # Outlet removal from updated bulk: 10 * (70/100) * 1 = 7
        # Net: 70 - 7 = 63
        assert state.liquid["A"] == pytest.approx(63.0)

    def test_mass_balance_over_many_steps(self) -> None:
        """C2: Mass balance converges with constant stream + default outflow.

        Recurrence: A_{n+1} = (A_n + 20) - 10*(A_n+20)/100 = 0.9*A_n + 18
        Steady state: A = 18/0.1 = 180.
        """
        state = ReactorState(volume=100.0, time=0.0)
        state.register_species("A", phase="liquid", initial=0.0)

        stream = InputStream(
            name="feed",
            flow_signal=Constant(10.0),
            composition={"A": Constant(2.0)},
        )
        process = MixingProcess(streams=[stream], outflow_rate=10.0)

        for i in range(200):
            state.time = float(i)
            process.execute(state, dt=1.0)

        assert state.liquid["A"] == pytest.approx(180.0, rel=0.02)
        assert state.volume == pytest.approx(100.0)

    def test_two_streams_independent_species(self) -> None:
        """C3: Two streams feeding different species simultaneously."""
        state = ReactorState(volume=100.0, time=0.0)
        state.register_species("A", phase="liquid", initial=0.0)
        state.register_species("B", phase="liquid", initial=0.0)

        stream_a = InputStream(
            name="FeedA",
            flow_signal=Constant(5.0),
            composition={"A": Constant(3.0)},
        )
        stream_b = InputStream(
            name="FeedB",
            flow_signal=Constant(2.0),
            composition={"B": Constant(10.0)},
        )
        process = MixingProcess(streams=[stream_a, stream_b])

        state.time = 0.0
        process.execute(state, dt=1.0)

        # total_in = 7, outflow = 7 (default)
        # A: 5*3*1 = 15 added, outflow removes 7 * (15/100) * 1 = 1.05 → A ≈ 13.95
        # B: 2*10*1 = 20 added, outflow removes 7 * (20/100) * 1 = 1.4 → B ≈ 18.6
        assert state.liquid["A"] == pytest.approx(13.95, rel=1e-3)
        assert state.liquid["B"] == pytest.approx(18.6, rel=1e-3)

    def test_explicit_outflow_volume_change(self) -> None:
        """C4: Explicit outflow different from total_in changes volume."""
        state = ReactorState(volume=100.0, time=0.0)
        state.register_species("A", phase="liquid", initial=50.0)

        stream = InputStream(
            name="feed",
            flow_signal=Constant(10.0),
            composition={"A": Constant(1.0)},
        )
        # outflow = 5, total_in = 10 → volume increases by (10-5)*1 = 5
        process = MixingProcess(streams=[stream], outflow_rate=5.0)

        state.time = 0.0
        process.execute(state, dt=1.0)

        assert state.volume == pytest.approx(105.0)

    def test_auto_register_new_species(self) -> None:
        """C5: Stream introducing a brand-new species auto-registers it.

        Inflow: 10*2*1 = 20 added → Novel=20.
        Outlet removal: 10*(20/100)*1 = 2 removed → Novel=18.
        """
        state = ReactorState(volume=100.0, time=0.0)
        # No species registered

        stream = InputStream(
            name="new_feed",
            flow_signal=Constant(10.0),
            composition={"Novel": Constant(2.0)},
        )
        process = MixingProcess(streams=[stream])

        state.time = 0.0
        process.execute(state, dt=1.0)

        assert "Novel" in state.liquid
        assert state.liquid["Novel"] == pytest.approx(18.0)

    def test_inactive_stream_no_contribution(self) -> None:
        """C6: Inactive stream contributes nothing."""
        state = ReactorState(volume=100.0, time=0.0)
        state.register_species("A", phase="liquid", initial=0.0)

        active_stream = InputStream(
            name="active",
            flow_signal=Constant(5.0),
            composition={"A": Constant(1.0)},
            active=True,
        )
        inactive_stream = InputStream(
            name="inactive",
            flow_signal=Constant(100.0),
            composition={"A": Constant(100.0)},
            active=False,
        )
        process = MixingProcess(streams=[active_stream, inactive_stream])

        state.time = 0.0
        process.execute(state, dt=1.0)

        # Only active stream contributes: 5*1*1 = 5 added
        # outflow = 5 (default), removes 5 * (5/100) * 1 = 0.25
        assert state.liquid["A"] == pytest.approx(4.75, rel=1e-3)

    def test_outflow_rate_signal(self) -> None:
        """Outflow as a Signal is evaluated each step."""
        state = ReactorState(volume=100.0, time=0.0)
        state.register_species("A", phase="liquid", initial=0.0)

        stream = InputStream(
            name="feed",
            flow_signal=Constant(10.0),
            composition={"A": Constant(1.0)},
        )
        process = MixingProcess(
            streams=[stream],
            outflow_rate=Step(baseline=5.0, step_value=15.0, step_time=10.0),
        )

        state.time = 0.0
        process.execute(state, dt=1.0)
        # outflow = 5, total_in = 10 → volume +5
        assert state.volume == pytest.approx(105.0)
        assert state.outflow_rate == pytest.approx(5.0)

        state.time = 10.0
        process.execute(state, dt=1.0)
        # outflow = 15, total_in = 10 → volume -5
        assert state.volume == pytest.approx(100.0)
        assert state.outflow_rate == pytest.approx(15.0)

    def test_state_inflows_recorded(self) -> None:
        """state.inflows is set correctly after execute."""
        state = ReactorState(volume=100.0, time=0.0)

        stream = InputStream(
            name="feed",
            flow_signal=Constant(10.0),
            composition={"A": Constant(2.0), "B": Constant(3.0)},
        )
        process = MixingProcess(streams=[stream])

        state.time = 0.0
        process.execute(state, dt=1.0)

        assert state.inflows == {"A": 20.0, "B": 30.0}
        assert state.outflow_rate == pytest.approx(10.0)
