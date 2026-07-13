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
