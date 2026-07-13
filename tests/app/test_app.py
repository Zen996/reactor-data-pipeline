from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest


def _find(widget_list, key):
    for w in widget_list:
        if w.key == key:
            return w
    return None


def _build_experiment(at: AppTest) -> None:
    """Helper: set up a minimal config and build."""
    _find(at.number_input, "n_reactions").set_value(0)
    _find(at.number_input, "sim_dt").set_value(0.5)
    _find(at.number_input, "sim_duration").set_value(5.0)
    _find(at.number_input, "sim_seed").set_value(42)
    btn = _find(at.button, "build_experiment_btn")
    btn.click().run()


def _advance_to(at: AppTest, target: float) -> None:
    _find(at.number_input, "run_target").set_value(target)
    btn = _find(at.button, "advance")
    btn.click().run()


def test_app_starts_with_config_form() -> None:
    at = AppTest.from_file("app/app.py")
    at.run()
    assert len(at.button) > 0
    assert any(b.label == "Build Experiment" for b in at.button)
    try:
        at.session_state["experiment"]
        assert False, "Experiment should not exist yet"
    except KeyError:
        pass


def test_build_experiment_populates_session() -> None:
    at = AppTest.from_file("app/app.py")
    at.run()
    _build_experiment(at)
    assert at.session_state["experiment"] is not None


def test_advance_produces_rows() -> None:
    at = AppTest.from_file("app/app.py")
    at.run()
    _build_experiment(at)

    _advance_to(at, 2.0)
    exp = at.session_state["experiment"]
    df = exp.recorder.to_dataframe()
    assert df.shape[0] == 5
    assert exp.engine.state.time == 2.0


def test_reset_clears_session() -> None:
    at = AppTest.from_file("app/app.py")
    at.run()
    _build_experiment(at)

    btn = _find(at.button, "sidebar_reset")
    btn.click().run()
    try:
        at.session_state["experiment"]
        assert False, "Experiment should have been cleared"
    except KeyError:
        pass


def test_rewind_truncates_rows() -> None:
    at = AppTest.from_file("app/app.py")
    at.run()
    _build_experiment(at)

    _advance_to(at, 4.0)
    exp_before = at.session_state["experiment"]
    rows_before = exp_before.recorder.to_dataframe().shape[0]

    _find(at.number_input, "rewind_target").set_value(2.0)
    btn = _find(at.button, "rewind_btn")
    btn.click().run()

    exp_after = at.session_state["experiment"]
    df_after = exp_after.recorder.to_dataframe()
    assert df_after.shape[0] < rows_before
    assert df_after["time"].max() <= 2.0
    assert exp_after.engine.state.time == 2.0


def test_rewind_before_zero_shows_warning() -> None:
    at = AppTest.from_file("app/app.py")
    at.run()
    _build_experiment(at)
    _advance_to(at, 2.0)

    _find(at.number_input, "rewind_target").set_value(-1.0)
    btn = _find(at.button, "rewind_btn")
    btn.click().run()
    warnings = at.warning
    assert len(warnings) > 0


def test_rewind_deterministic_reproduces() -> None:
    at = AppTest.from_file("app/app.py")
    at.run()
    _build_experiment(at)

    _advance_to(at, 4.0)
    df1 = at.session_state["experiment"].recorder.to_dataframe()

    _find(at.number_input, "rewind_target").set_value(2.0)
    btn = _find(at.button, "rewind_btn")
    btn.click().run()

    _advance_to(at, 4.0)
    df2 = at.session_state["experiment"].recorder.to_dataframe()

    assert (
        df1[df1["time"] > 2.0].values == pytest.approx(
            df2[df2["time"] > 2.0].values, rel=1e-10
        )
    )


def test_two_feeds_plus_reaction_produces_c() -> None:
    """Configure 2 feed streams (A constant, B square wave) that react
    A+2B→C, then verify C is produced and the square wave oscillates."""
    at = AppTest.from_file("app/app.py")
    at.run()

    # Configure 3 species: A, B, C (all start at 0, stream-fed)
    at.session_state["n_species"] = 3
    for i, name in enumerate(["A", "B", "C"]):
        at.session_state[f"species_{i}_name"] = name
        at.session_state[f"species_{i}_phase"] = "liquid"
        at.session_state[f"species_{i}_qty"] = 0.0

    # 2 streams
    at.session_state["n_streams"] = 2

    # Stream 0: feed_A — constant flow, constant composition A
    at.session_state["stream_0_name"] = "feed_A"
    at.session_state["stream_0_phase"] = "liquid"
    at.session_state["stream_0_flow_type"] = "constant"
    at.session_state["stream_0_flow_value"] = 0.5
    at.session_state["stream_0_n_comp"] = 1
    at.session_state["stream_0_comp_0_sp"] = "A"
    at.session_state["stream_0_comp_0_type"] = "constant"
    at.session_state["stream_0_comp_0_value"] = 2.0
    at.session_state["stream_0_active"] = True

    # Stream 1: feed_B — square wave flow, constant composition B
    at.session_state["stream_1_name"] = "feed_B"
    at.session_state["stream_1_phase"] = "liquid"
    at.session_state["stream_1_flow_type"] = "square"
    at.session_state["stream_1_flow_amp"] = 0.5
    at.session_state["stream_1_flow_freq"] = 0.05
    at.session_state["stream_1_flow_offset"] = 1.0
    at.session_state["stream_1_n_comp"] = 1
    at.session_state["stream_1_comp_0_sp"] = "B"
    at.session_state["stream_1_comp_0_type"] = "constant"
    at.session_state["stream_1_comp_0_value"] = 1.0
    at.session_state["stream_1_active"] = True

    # 1 reaction
    at.session_state["n_reactions"] = 1
    at.session_state["reaction_0_reactants"] = "A:1,B:2"
    at.session_state["reaction_0_products"] = "C:1"
    at.session_state["reaction_0_k"] = 0.2

    # Simulation params
    at.session_state["sim_dt"] = 0.5
    at.session_state["sim_duration"] = 30.0
    at.session_state["sim_seed"] = 42
    at.session_state["sim_volume"] = 1.0

    # Build
    btn = _find(at.button, "build_experiment_btn")
    btn.click().run()

    exp = at.session_state["experiment"]
    assert exp is not None

    # Advance to see square wave oscillation
    _advance_to(at, 15.0)
    exp = at.session_state["experiment"]
    df = exp.recorder.to_dataframe()

    # --- Assertions ---

    # C was produced
    assert "liquid.C" in df.columns
    assert df["liquid.C"].iloc[-1] > 0.0

    # Square wave flow rate should oscillate between 0.5 and 1.5
    fr_col = "derived.stream.feed_B.flow_rate"
    assert fr_col in df.columns
    fr_values = df[fr_col].unique()
    assert 0.5 in fr_values
    assert 1.5 in fr_values

    # Constant feed should stay at steady value
    const_col = "derived.stream.feed_A.flow_rate"
    assert const_col in df.columns
    assert df[const_col].nunique() == 1
    assert df[const_col].iloc[0] == 0.5

    # Both feed inflow rates recorded
    assert "derived.stream.feed_A.inflow.A" in df.columns
    assert "derived.stream.feed_B.inflow.B" in df.columns

    # Outlet rates recorded
    assert "derived.outlet.A" in df.columns
    assert "derived.outlet.B" in df.columns
    assert "derived.outlet.C" in df.columns
