from __future__ import annotations

import json
import os
import tempfile

import pandas as pd
import pytest
import yaml

from config.builder import build_engine, build_signal
from config.reactions import DecayConfig, EquilibriumConfig, ReactionConfig
from config.simulation import SimulationConfig
from config.species import SpeciesConfig
from core.random_manager import RandomManager


def _simple_config() -> SimulationConfig:
    return SimulationConfig(
        species=[
            SpeciesConfig(name="A", phase="liquid", initial_quantity=10.0),
            SpeciesConfig(name="B", phase="liquid", initial_quantity=0.0),
        ],
        streams=[
            {
                "name": "feed",
                "phase": "liquid",
                "flow_signal": {"type": "constant", "value": 0.5},
                "composition": {"A": {"type": "constant", "value": 1.0}},
            }
        ],
        reactions=[
            ReactionConfig(
                reactants={"A": 1},
                products={"B": 1},
                rate_constant=0.2,
            )
        ],
        dt=0.2,
        duration=2.0,
        seed=42,
    )


class TestBuildEngine:
    def test_end_to_end_smoke(self) -> None:
        config = _simple_config()
        engine = build_engine(config)
        engine.run()
        df = engine._config_recorder.to_dataframe()
        assert df.shape[0] == 10
        for col in ["sim_time", "volume", "liquid.A", "liquid.B"]:
            assert col in df.columns

    def test_two_different_configs(self) -> None:
        config_a = _simple_config()

        config_b = SimulationConfig(
            species=[
                SpeciesConfig(name="X", phase="liquid", initial_quantity=5.0),
                SpeciesConfig(name="Y", phase="vapor", initial_quantity=3.0),
            ],
            streams=[
                {
                    "name": "feed",
                    "phase": "liquid",
                    "flow_signal": {"type": "constant", "value": 0.1},
                    "composition": {"X": {"type": "constant", "value": 2.0}},
                }
            ],
            reactions=[],
            dt=0.5,
            duration=5.0,
            seed=7,
        )

        engine_a = build_engine(config_a)
        engine_a.run()
        df_a = engine_a._config_recorder.to_dataframe()

        engine_b = build_engine(config_b)
        engine_b.run()
        df_b = engine_b._config_recorder.to_dataframe()

        assert df_a.shape[0] == 10
        assert df_b.shape[0] == 10
        assert set(df_a.columns) != set(df_b.columns)


class TestLoadRoundtrip:
    def test_json_roundtrip(self) -> None:
        config = _simple_config()
        d = {
            "species": [{"name": s.name, "phase": s.phase, "initial_quantity": s.initial_quantity} for s in config.species],
            "streams": [{"name": "feed", "phase": "liquid", "flow_signal": {"type": "constant", "value": 0.5}, "composition": {"A": {"type": "constant", "value": 1.0}}}],
            "reactions": [{"reactants": {"A": 1}, "products": {"B": 1}, "rate_constant": 0.2}],
            "dt": 0.2, "duration": 2.0, "seed": 42,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cfg.json")
            with open(path, "w") as f:
                json.dump(d, f)
            loaded = SimulationConfig.load(path)
        assert loaded.dt == 0.2
        assert loaded.seed == 42
        assert len(loaded.species) == 2

    def test_yaml_roundtrip(self) -> None:
        d = {
            "species": [{"name": "A", "phase": "liquid", "initial_quantity": 10.0}],
            "streams": [{"name": "feed", "phase": "liquid", "flow_signal": {"type": "constant", "value": 1.0}, "composition": {"A": {"type": "constant", "value": 1.0}}}],
            "dt": 0.5, "duration": 5.0, "seed": 99,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cfg.yaml")
            with open(path, "w") as f:
                yaml.dump(d, f)
            loaded = SimulationConfig.load(path)
        assert loaded.dt == 0.5
        assert loaded.seed == 99
        assert loaded.species[0].name == "A"

    def test_json_yaml_match(self) -> None:
        d = {
            "species": [{"name": "A", "phase": "liquid", "initial_quantity": 5.0}],
            "streams": [{"name": "feed", "phase": "liquid", "flow_signal": {"type": "constant", "value": 1.0}, "composition": {"A": {"type": "constant", "value": 2.0}}}],
            "dt": 0.1, "duration": 1.0, "seed": 0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            jp = os.path.join(tmp, "c.json")
            with open(jp, "w") as f:
                json.dump(d, f)
            yp = os.path.join(tmp, "c.yaml")
            with open(yp, "w") as f:
                yaml.dump(d, f)
            from_json = SimulationConfig.load(jp)
            from_yaml = SimulationConfig.load(yp)
        assert from_json.dt == from_yaml.dt
        assert from_json.seed == from_yaml.seed
        assert from_json.species[0].name == from_yaml.species[0].name


class TestReproducibility:
    def test_gaussian_noise_reproducible(self) -> None:
        cfg = _simple_config()
        cfg.sensors = [
            {
                "species": "A",
                "phase": "liquid",
                "noise": {"type": "gaussian_noise", "std": 0.1},
                "output_key": "sensor_A",
            }
        ]
        engine1 = build_engine(cfg)
        engine1.run()
        df1 = engine1._config_recorder.to_dataframe()

        engine2 = build_engine(cfg)
        engine2.run()
        df2 = engine2._config_recorder.to_dataframe()

        pd.testing.assert_frame_equal(df1, df2)


class TestBuildSignal:
    def test_composite_signal(self) -> None:
        spec = {
            "type": "composite",
            "segments": [
                {"start": 0.0, "end": 5.0, "signal": {"type": "constant", "value": 1.0}},
                {"start": 5.0, "end": 10.0, "signal": {"type": "constant", "value": 2.0}},
            ],
        }
        sig = build_signal(spec)
        assert sig.value(0.0) == 1.0
        assert sig.value(5.0) == 2.0
        assert sig.value(7.5) == 2.0

    def test_all_simple_types(self) -> None:
        specs = [
            {"type": "constant", "value": 3.14},
            {"type": "step", "baseline": 0.0, "step_value": 5.0, "step_time": 2.0},
            {"type": "ramp", "start_value": 0.0, "slope": 1.0},
            {"type": "sinusoid", "amplitude": 1.0, "frequency": 0.01},
            {"type": "square", "amplitude": 1.0, "frequency": 0.01},
            {"type": "triangle", "amplitude": 1.0, "frequency": 0.01},
            {"type": "gaussian_noise", "std": 0.1},
            {"type": "uniform_noise", "low": -0.1, "high": 0.1},
        ]
        for spec in specs:
            sig = build_signal(spec)
            val = sig.value(0.0)
            assert isinstance(val, float)

    def test_noise_build_signal_uses_generator(self) -> None:
        spec = {"type": "gaussian_noise", "std": 0.1}
        rm = RandomManager(seed=42)
        sig1 = build_signal(spec, rm, "test.noise")
        sig2 = build_signal(spec, rm, "test.noise2")
        val1 = sig1.value(0.0)
        val2 = sig2.value(0.0)
        assert val1 != val2


class TestTwoFeedReaction:
    """End-to-end: two steady feed streams of A and B react to produce C."""

    def test_two_feeds_produce_c(self) -> None:
        """A + 2B → C with steady feeds of A and B should yield C in the output."""
        cfg = SimulationConfig(
            species=[
                SpeciesConfig(name="A", phase="liquid", initial_quantity=0.0),
                SpeciesConfig(name="B", phase="liquid", initial_quantity=0.0),
                SpeciesConfig(name="C", phase="liquid", initial_quantity=0.0),
            ],
            streams=[
                {
                    "name": "feed_A",
                    "phase": "liquid",
                    "flow_signal": {"type": "constant", "value": 0.5},
                    "composition": {"A": {"type": "constant", "value": 2.0}},
                    "active": True,
                },
                {
                    "name": "feed_B",
                    "phase": "liquid",
                    "flow_signal": {"type": "constant", "value": 0.5},
                    "composition": {"B": {"type": "constant", "value": 1.0}},
                    "active": True,
                },
            ],
            reactions=[
                ReactionConfig(
                    reactants={"A": 1, "B": 2},
                    products={"C": 1},
                    rate_constant=0.2,
                )
            ],
            dt=0.2,
            duration=10.0,
            seed=42,
        )
        engine = build_engine(cfg)
        engine.run()
        df = engine._config_recorder.to_dataframe()

        # All three species should be present as recorded columns
        assert "liquid.A" in df.columns
        assert "liquid.B" in df.columns
        assert "liquid.C" in df.columns

        # C should have been produced (positive quantity at the end)
        assert df["liquid.C"].iloc[-1] > 0.0

        # Feed stream flow rates should have been recorded
        assert "derived.stream.feed_A.flow_rate" in df.columns
        assert "derived.stream.feed_B.flow_rate" in df.columns

        # Per-species inflow rates should be present
        assert "derived.stream.feed_A.inflow.A" in df.columns
        assert "derived.stream.feed_B.inflow.B" in df.columns

        # Outlet species should be recorded
        assert "derived.outlet.A" in df.columns
        assert "derived.outlet.B" in df.columns
        assert "derived.outlet.C" in df.columns
