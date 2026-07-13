# CSTR Simulation GUI

Streamlit-based interactive front-end for the configurable dynamic
simulation engine (Stages 1–12).

## Quick Start

```bash
streamlit run app/app.py
```

## Walkthrough

1. **Configure** — In the sidebar, add species, streams (with signal
   types and composition), reactions, and set simulation parameters
   (dt, duration, seed, volume). Click **Build Experiment**.

2. **Advance** — Use the "Step once" or "Advance" buttons to run the
   simulation forward. Charts update live in the main panel:
   - *Input Streams*: per-stream flow rates and species inflows.
   - *Reactor / Output*: species quantities (liquid/vapor), outlet
     rates, reaction rates, sensor readings.

3. **Live Tweaks** — Open expandable sections under "Live Parameters"
   to edit stream active flags, flow/composition signals, or reaction
   rate constants. Edits take effect on the **next** step without
   rebuilding the experiment.

4. **Rewind** — Enter a target time and click **Rewind**. The simulation
   state, recorder, and manipulation firing history are reverted to that
   point. User edits (stream toggles, rate constant changes) are
   **preserved** across the rewind. A warning appears if randomness is
   enabled (noise signals), since a rewind-then-continue will not
   reproduce the original continuation.

5. **Export** — Download CSV or Parquet of the current recorded data at
   any time via the sidebar buttons.

6. **Reset** — Clears the experiment and returns to the config form.

## Manual QA Checklist

- [ ] Input-stream and reactor charts render legibly and update after
      each Advance click.
- [ ] Download buttons produce CSV and Parquet files that open correctly
      in a spreadsheet or pandas.
- [ ] Rapid repeated clicking of "Advance" / "Apply" doesn't duplicate
      rows or desync the displayed chart from the current time.

## Architecture

- `app.py` — Entry point, layout, dispatch.
- `session.py` — `st.session_state` helpers.
- `checkpoints.py` — `CheckpointStore` for rewind support.
- `views/config_editor.py` — Sidebar form to build a `SimulationConfig`.
- `views/run_controls.py` — Step/Advance/Rewind/Reset controls.
- `views/live_params.py` — Expandable live-editing forms for
  streams, reactions, and manipulations.
- `views/charts.py` — Plot input-stream and reactor/output time series
  using `analysis/timeseries.py`.
