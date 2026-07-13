"""End-to-end integration tests covering all major process combinations.

Each test builds a simulation from a preset config, runs it, and checks
that the output is physically sensible.
"""

from config.presets import PRESETS
from config.simulation import SimulationConfig
from config.builder import build_engine


def _run_preset(name: str):
    cfg = SimulationConfig.from_dict(PRESETS[name])
    engine = build_engine(cfg)
    engine.run()
    return engine._config_recorder.to_dataframe()


class TestFirstOrderReaction:
    def test_constant_feed(self) -> None:
        df = _run_preset("first_order_constant")
        assert "liquid.A" in df.columns
        assert "liquid.B" in df.columns
        # B should be produced
        assert df["liquid.B"].iloc[-1] > 0.0
        # Steady state reached
        assert abs(df["liquid.B"].iloc[-1] - df["liquid.B"].iloc[-3]) < 1e-4

    def test_step_feed(self) -> None:
        df = _run_preset("first_order_step")
        # Feed starts at t=5; B should be near zero early and rise after
        early_b = df.loc[df["time"] < 4.0, "liquid.B"].mean()
        late_b = df.loc[df["time"] > 10.0, "liquid.B"].mean()
        assert late_b > early_b, "B should increase after step feed turns on"

    def test_ramp_feed(self) -> None:
        df = _run_preset("first_order_ramp")
        # Both A and B should increase over the ramp period
        assert df["liquid.A"].iloc[-1] > df["liquid.A"].iloc[2]
        assert df["liquid.B"].iloc[-1] > df["liquid.B"].iloc[2]

    def test_sinusoid_feed(self) -> None:
        df = _run_preset("first_order_sinusoid")
        # B should oscillate in response to the sinusoidal feed
        vals = df["liquid.B"].values
        # There should be both increase and decrease (oscillation)
        diffs = [vals[i] - vals[i - 1] for i in range(5, len(vals))]
        n_positive = sum(1 for d in diffs if d > 0)
        n_negative = sum(1 for d in diffs if d < 0)
        assert n_positive > 0 and n_negative > 0, "B should oscillate"


class TestSecondOrderReaction:
    def test_two_A_to_B(self) -> None:
        df = _run_preset("second_order_2A_to_B")
        assert "liquid.B" in df.columns
        # B should increase over time (second-order from A)
        assert df["liquid.B"].iloc[-1] > df["liquid.B"].iloc[0]

    def test_A_plus_B_to_C(self) -> None:
        df = _run_preset("second_order_A_plus_B")
        assert "liquid.C" in df.columns
        # C should be produced
        assert df["liquid.C"].iloc[-1] > 0.0
        # Both A and B should exist in the reactor
        assert df["liquid.A"].iloc[-1] >= 0.0
        assert df["liquid.B"].iloc[-1] >= 0.0


class TestFirstOrderDecay:
    def test_decay_with_product(self) -> None:
        df = _run_preset("decay_with_product")
        assert "liquid.A" in df.columns
        assert "liquid.B" in df.columns
        # B should be produced from decay
        assert df["liquid.B"].iloc[-1] > 0.0
        # Decay rate should be recorded
        assert "derived.decay_rate_A" in df.columns


class TestVaporEquilibrium:
    def test_equilibrium_reached(self) -> None:
        df = _run_preset("vapor_equilibrium")
        assert "liquid.X" in df.columns
        assert "vapor.X" in df.columns
        # Both phases should have positive amounts
        assert df["liquid.X"].iloc[-1] > 0.0
        assert df["vapor.X"].iloc[-1] > 0.0
        # Equilibrium net should be recorded
        assert "derived.equilibrium_net_X" in df.columns


class TestAllPresetsSmoke:
    """Minimal smoke test — every preset runs without error."""

    def test_all_presets_run(self) -> None:
        for name in PRESETS:
            df = _run_preset(name)
            assert df.shape[0] > 0, f"Preset {name} produced no data"
