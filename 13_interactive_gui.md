# Stage 13 — Interactive GUI (Streamlit)

## Context

Stages 1–12 give you a complete, config-driven simulator with tabular
export and a standalone analysis toolkit. This stage adds a Streamlit app
on top, letting a person build an experiment, run it forward to any point
in time, **pause**, tweak a live parameter (a signal, a reaction rate, a
manipulation), and **continue the same run from that point** — not restart
from t=0. It then charts input streams (feed flows/composition) and
output/reactor variables (species, volume, reaction rates) as they
accumulate.

This is a GUI layer only. It must not duplicate simulation logic — it
calls into `config/builder.py`, `core/engine.py`, and `analysis/*.py`
exactly as any other consumer of the library would.

## Prerequisite Amendments to Earlier Stages

These are small, backward-compatible additions — not rewrites. Existing
tests from those stages must keep passing unmodified.

### 1. `core/engine.py` — expose stepping

```python
class SimulationEngine:
    def step(self) -> None:
        """Execute exactly one timestep at the current clock: run every
        process once, record once, then advance the clock by dt. This is
        the primitive `run()` already implied but never exposed
        publicly."""

    def run_until(self, target_time: float) -> None:
        """Call step() repeatedly while self.current_time < target_time
        AND self.current_time < self.duration — i.e. never steps past the
        configured duration, but can stop early at any intermediate
        target_time. Safe to call repeatedly with increasing target_time
        values across many GUI interactions."""

    def run(self) -> None:
        """Now implemented as self.run_until(self.duration). Public
        behavior for existing Stage 1 callers/tests is unchanged."""
```

### 2. `processes/mixing.py` — record per-stream detail

Currently `state.derived` gets whatever `ReactionProcess`/`DecayProcess`
write, plus aggregate `state.inflows`/`state.outflow_rate`. Add, per step:

- `state.derived[f"stream.{stream.name}.flow_rate"] = stream.flow_rate(t)`
- `state.derived[f"stream.{stream.name}.inflow.{species}"] = rate` for
  each species in that stream's composition
- `state.derived[f"outlet.{species}"] = outflow_rate *
  state.concentration(species)` for each liquid species

This is additive (new keys only) so it doesn't break Stage 5/10 tests. It
exists because the GUI needs to plot *individual* input streams and the
outlet stream, not just the aggregate — and because once noise or
manipulations can toggle a stream's `active` flag mid-run, the aggregate
alone can't be un-mixed after the fact.

### 3. `config/builder.py` — expose live handles

Add a new function alongside the existing `build_engine` (don't change
`build_engine`'s signature or return type — Stage 11's tests depend on it):

```python
@dataclass
class BuiltExperiment:
    config: "SimulationConfig"
    state: "ReactorState"
    engine: "SimulationEngine"
    random_manager: "RandomManager"
    streams: list        # list[InputStream]  — same objects MixingProcess holds
    reactions: list       # list[Reaction]      — same objects ReactionProcess holds
    decays: list
    equilibria: list
    manipulations: list   # list[Manipulation]
    recorder: "TabularRecorder"

def build_experiment(config: "SimulationConfig") -> BuiltExperiment:
    """Same assembly as build_engine, but constructs each component list
    once and passes the *same* object instances both into their Process
    (e.g. MixingProcess(streams=streams)) and into the returned
    BuiltExperiment. This shared-reference property is what makes live
    tweaking work: mutating experiment.reactions[0].rate_constant changes
    what ReactionProcess sees on the next step, with no rebuild."""
```

### 4. `core/engine.py` — atomic state/clock restore (for rewind)

```python
class SimulationEngine:
    def restore(self, state, time: float) -> None:
        """Replace the engine's live state object and reset its clock to
        `time` in a single atomic call, so the two can never drift out of
        sync. This is the only way state/time should ever move backward —
        ordinary forward stepping (step()/run_until()) never calls this,
        and callers of restore() are responsible for passing a `state`
        that is actually valid at `time` (e.g. a prior checkpoint's
        copy())."""
```

### 5. `recorder/recorder.py` — truncate on rewind

```python
class TabularRecorder:
    def truncate_after(self, time: float) -> None:
        """Drop every buffered row with recorded time strictly greater
        than `time`, keeping the row at `time` itself if one exists. Used
        when rewinding: the persistent/exported record always reflects a
        single linear timeline (the currently active branch), never a
        tree of branches — rows from an abandoned future are discarded
        permanently, not retained anywhere."""
```

### 6. `processes/manipulation.py` — time-stamped one-shot firing

Stage 8 left the internal representation of "has this one-shot
manipulation already fired" unspecified. Make it explicit and
time-stamped rather than a bare boolean, since rewind needs to know *when*
it fired, not just whether:

```python
@dataclass
class Manipulation:
    trigger: Trigger
    action: Action
    one_shot: bool = False
    fired_at: float | None = None
    """Sim time at which this manipulation last fired, if one_shot and it
    has fired. None means "hasn't fired yet". ManipulationProcess treats
    `fired_at is not None` as the suppression condition for one_shot
    manipulations, and sets `fired_at = state.time` on firing."""
```

This is additive/clarifying, not breaking — Stage 8's acceptance criteria
only check externally observable firing behavior, not the internal
representation, so existing tests are unaffected.

## Goal

A single-page Streamlit app: configure an experiment in a sidebar, run it
forward in controlled increments, tweak live parameters between
increments, and watch input/output charts grow continuously across the
whole session.

## Files to Create

```
app/
    app.py                # entry point (`streamlit run app/app.py`)
    session.py             # st.session_state helpers
    checkpoints.py          # CheckpointStore for branch-only rewind
    views/
        config_editor.py    # sidebar forms -> SimulationConfig
        run_controls.py      # step/run-to/apply-and-continue/rewind controls
        live_params.py        # forms to edit live streams/reactions/etc.
        charts.py             # input-stream and output-variable charts
```

## Behavior / Layout

```python
# app/session.py
import streamlit as st

def get_experiment() -> "BuiltExperiment | None":
    return st.session_state.get("experiment")

def set_experiment(experiment: "BuiltExperiment") -> None:
    st.session_state["experiment"] = experiment
    st.session_state["checkpoints"] = CheckpointStore()

def reset() -> None:
    st.session_state.pop("experiment", None)
    st.session_state.pop("checkpoints", None)
```

```python
# app/checkpoints.py
from dataclasses import dataclass

@dataclass
class Checkpoint:
    time: float
    state: "ReactorState"   # a .copy() taken at that time

class CheckpointStore:
    """Time-ordered list of ReactorState snapshots, one per recorded
    step. Lightweight: ReactorState is a few dicts of floats, so keeping
    one per step is cheap even for long runs. If that ever becomes a
    real memory concern, thin it to every Nth step — not needed by
    default."""

    def __init__(self) -> None:
        self._checkpoints: list[Checkpoint] = []

    def add(self, time: float, state: "ReactorState") -> None:
        """Call once per recorded step during normal forward
        advancement (state.copy(), not the live reference)."""

    def nearest_at_or_before(self, time: float) -> "Checkpoint | None":
        """Latest checkpoint with checkpoint.time <= time. Checkpoints
        are time-ordered, so this is a simple bisect."""

    def drop_after(self, time: float) -> None:
        """Discard checkpoints past `time`. Called after a rewind so a
        later rewind attempt can't target a time that only existed on
        the now-abandoned branch."""
```

```python
# app/app.py (control flow, not literal code)
1. Sidebar: config_editor.render() -> a SimulationConfig built from form
   inputs (species table, streams with signal-type dropdowns + params,
   reactions, decays, equilibria, manipulations, dt/duration/seed).
2. "Build Experiment" button -> config.builder.build_experiment(config),
   store via session.set_experiment(...). Disabled/hidden once an
   experiment already exists this session (show "Reset" instead) so a
   stray rerun can't silently rebuild and lose progress.
3. If an experiment exists:
   a. run_controls.render(experiment, checkpoints): a number input or
      slider for "run to time", bounded [experiment.state.time,
      config.duration], plus an "Advance" button. Each call to
      engine.step() inside that advance is immediately followed by
      checkpoints.add(state.time, state.copy()) so every reached point
      becomes a valid future rewind target. Also offer a "Step once"
      button for fine control, and a separate "Rewind to time" input
      bounded [0, experiment.state.time] with its own button (see below).
   b. live_params.render(experiment): expandable sections per component
      (one per stream/reaction/decay/equilibrium/manipulation) with
      editable fields; an "Apply" button mutates the live object's
      attributes in place (e.g. `experiment.streams[i].flow_signal =
      new_signal_instance`, `experiment.reactions[j].rate_constant =
      new_value`). No rebuild, no reset — this only affects steps taken
      *after* the edit.
   c. charts.render(experiment): pull
      experiment.recorder.to_dataframe() fresh each rerun (cheap — it's
      an in-memory buffer) and plot:
        - input streams: one line per stream's
          `stream.{name}.flow_rate` / `.inflow.{species}` columns
        - reactor/output: liquid & vapor species concentrations, volume,
          `outlet.{species}` columns, and any `reaction_rate_*`/sensor
          columns present
      Use `analysis/timeseries.py`'s `plot_timeseries` (wrapped in
      `st.pyplot(fig)`) so charting logic isn't duplicated between the
      library and the app.
   d. Download buttons for CSV/Parquet/metadata via the recorder's
      existing export methods, writing to a temp path and using
      `st.download_button` with the file's bytes.
4. "Reset" button -> session.reset(), returns to the config-only view.

# Rewind control (part of run_controls.render()):
5. On "Rewind to time T" click:
   a. checkpoint = checkpoints.nearest_at_or_before(T)
      (surface the *actual* landed time in the UI if it differs from T —
      checkpoint granularity is per-recorded-step, so this should only
      differ when T falls strictly between two steps)
   b. experiment.engine.restore(checkpoint.state.copy(), checkpoint.time)
   c. experiment.recorder.truncate_after(checkpoint.time)
   d. checkpoints.drop_after(checkpoint.time)
   e. For m in experiment.manipulations: if m.fired_at is not None and
      m.fired_at > checkpoint.time: m.fired_at = None. This lives in the
      GUI layer, not in engine.restore() — the engine must stay ignorant
      of what a Manipulation even is (Stage 1's "no process-specific
      logic" invariant), so this loop operates directly on
      experiment.manipulations, the same shared-reference list
      ManipulationProcess holds.
   f. Live-edited parameters (stream active flags, reaction rate
      constants, signal instances swapped in via live_params) are
      deliberately left untouched by rewind — they're user decisions, not
      system bookkeeping, and stay sticky exactly like they do during
      normal forward advancement. Only step (e)'s time-stamped one-shot
      flags get reset, because those exist purely to implement
      trigger-time semantics, not to record a choice anyone made.
   g. If any noise/stochastic signal is configured anywhere in the
      experiment, show a persistent small notice near the charts:
      "Randomness is enabled — continuing from a rewind will not
      reproduce the original run past this point." This is a
      documented characteristic of branch-only rewind, not an error
      state, but it must not be silent.
```

## Behavioral Requirements

- **Never rebuild the experiment on a plain rerun.** Streamlit reruns the
  whole script on every widget interaction; the experiment must live in
  `st.session_state` and only be (re)constructed on an explicit "Build" or
  "Reset" click, never implicitly.
- **Mutate, don't replace, list contents.** The live-parameter forms must
  mutate attributes on the existing objects in `experiment.streams` /
  `.reactions` / etc. in place. Replacing an entire list (e.g.
  `experiment.reactions = [...]`) breaks the shared-reference contract
  with `ReactionProcess` and silently stops working — call this out with
  a code comment wherever a form applies an edit.
- **`run_until`'s "advance" path never moves backward.** Clamp the
  "run to time" input's minimum to `experiment.state.time`. Moving
  backward is only ever done through the dedicated Rewind control
  (`engine.restore(...)`), never through `run_until`, so the two
  mechanisms can't be confused with each other in the code or the UI.
- **Rewind truncates, it doesn't branch-and-keep.** A rewind always calls
  `recorder.truncate_after(...)` and `checkpoints.drop_after(...)` in the
  same action as `engine.restore(...)`. The exported/persistent dataset
  is a single linear timeline at all times — there is no mechanism in
  this stage to retain or compare an abandoned future after rewinding
  past it (see Out of Scope).
- **Rewind resets time-stamped system bookkeeping, but never touches
  user-driven live edits.** One-shot manipulations' `fired_at` is reset
  to `None` whenever it's after the rewind point, because that flag
  exists purely to implement deterministic trigger-time semantics — it's
  not a decision anyone made, and leaving it stale would make the
  reactor's contents and the equipment's bookkeeping inconsistent with
  each other for no reason. Stream `active` toggles, reaction rate
  constants, and swapped-in signal instances set via `live_params` are
  the opposite: they're intentional user edits, and rewind must leave
  them exactly as they are, for the same reason those edits are sticky
  during ordinary forward advancement in the first place.
- **No reproducibility guarantee across a rewound branch when randomness
  is configured.** RNG generators (Stage 9) are not checkpointed or
  restored — they simply continue emitting from their current internal
  state. A rewind-then-continue with no parameter changes is *not*
  expected to reproduce the original (now-discarded) continuation once
  any noise source is in play; it will, however, be identical in the
  fully deterministic case, which is worth asserting in tests as a sanity
  check that rewind itself isn't introducing unrelated drift.
- Charts must reflect exactly what's been recorded so far — no
  interpolation or prediction past `experiment.state.time`.
- All widget keys must be unique and stable across reruns (Streamlit
  requirement) — namespace them by component index/name
  (e.g. `key=f"reaction_{j}_rate_constant"`).
- The app must not import or reimplement anything from `analysis/` or
  `config/builder.py` — it calls them.

## Out of Scope

- **Exact replay / undo.** Rewind is branch-only (see Behavioral
  Requirements): it restores `ReactorState`, truncates the record, and
  re-syncs one-shot manipulation timing, but does not checkpoint RNG
  generator state. A byte-identical replay of a rewound-and-continued run
  is out of scope whenever any noise source is configured; if that's ever
  needed, it requires additionally checkpointing each noise source's
  `Generator.bit_generator.state` alongside the `ReactorState` copy — a
  bounded but real addition, not built here. In a fully deterministic
  experiment (no noise anywhere), rewind-then-continue-with-no-edits *is*
  expected to reproduce the original run exactly — that's the guarantee
  Acceptance Criteria #7 checks.
- **Keeping or comparing an abandoned branch.** Rewinding permanently
  discards the record past the rewind point (`truncate_after` +
  `drop_after`). There is no multi-branch view, diff, or tree in this
  stage — only ever one active linear timeline.
- Multi-user/session persistence across browser reloads — a session's
  experiment lives only in that Streamlit session's memory, same as any
  other `st.session_state` data.
- Real-time/streaming updates without user interaction (e.g.
  auto-advancing on a timer) — every advance is user-triggered.
- Editing `SpeciesConfig` (adding/removing species) after the experiment
  is built — species set is fixed at build time for this stage; only
  numeric/signal parameters on existing components are live-editable.

## Acceptance Criteria

Use `streamlit.testing.v1.AppTest` for automated checks, plus one manual
QA pass (Streamlit apps are only partially testable headlessly):

`tests/app/test_app.py`:

1. `AppTest.from_file("app/app.py").run()` succeeds without an
   uncaught exception, and shows the config form with no experiment yet
   built.
2. Programmatically fill in a minimal config (one species, one constant
   stream, no reactions) and click "Build Experiment" — assert
   `session.get_experiment()` is populated after the run.
3. Click "Advance" with a target time — assert
   `experiment.recorder.to_dataframe()` has the expected number of rows
   and `experiment.state.time` matches the target.
4. **Core behavior test**: advance to `t=T1`, note the recorded DataFrame;
   edit a live stream's flow value upward via the live-params form, click
   Apply, advance to `t=T2`; assert (a) all rows with `time < T1` are
   byte-identical to before the edit, and (b) the slope of the relevant
   `stream.*.flow_rate` column strictly increases after `T1` compared to
   before it.
5. "Reset" clears the session and returns to the config-only view.
6. **Rewind + truncate**: advance to `t=T2`, rewind to an earlier `t=T1`
   — assert `experiment.recorder.to_dataframe()["time"].max() <= T1`
   (rows past T1 are gone) and `experiment.state.time == T1`.
7. **Rewind + continue, deterministic case**: with no noise anywhere in
   the config, advance to `T2`, record the DataFrame, rewind to `T1`,
   continue to `T2` again with no edits — assert the resulting rows for
   `time` in `(T1, T2]` are identical to the original run's rows in that
   range. This must hold generally, including when a one-shot
   manipulation's trigger falls inside `(T1, T2]` — that's exactly what
   criterion #7a below isolates.
7a. **One-shot re-arming across a rewind**: configure a one-shot
   manipulation whose trigger fires inside `(T1, T2]`; advance past it to
   `T2`, rewind to `T1` (before its fire time), continue to `T2` again
   with no edits — assert `fired_at` was reset to `None` on rewind, the
   manipulation fires again during the second pass, and its effect on the
   resulting rows matches the original run exactly (this is the case that
   used to be a footgun before the `fired_at` fix; it must not be treated
   as an expected-divergence case like the stochastic scenario in #8).
8. **Rewind + continue, stochastic case**: same as above but with a
   `gaussian_noise`-driven signal configured — assert the two
   continuations are *allowed* to differ (i.e. don't assert equality;
   just confirm the run completes and produces valid, non-crashing
   output), and assert the "randomness enabled" notice is shown.
9. A rewind target earlier than any existing checkpoint (e.g. before
   `t=0`) is clamped or rejected with a clear message, never a crash.
10. **Live edits stay sticky across a rewind**: toggle a stream's
   `active` flag off via `live_params` at some time before `T1`, then
   rewind to `T1` — assert the stream is still inactive after the
   rewind (rewind must not have any code path that touches
   `experiment.streams[i].active`, `reaction.rate_constant`, or any other
   live-edited attribute; only `ReactorState`, the recorder, the
   checkpoint store, and manipulations' `fired_at` are touched).

Manual QA checklist (documented in `app/README.md`, not automated):

- Visual check that input-stream and output/reactor charts render legibly
  and update after each Advance click.
- Download buttons produce a CSV and Parquet file that open correctly.
- Rapid repeated clicking of "Advance"/"Apply" doesn't duplicate rows or
  desync the displayed chart from `experiment.state.time`.

## Example

`app/README.md`: a short walkthrough — run `streamlit run app/app.py`,
build a two-species, one-reaction experiment, advance to `t=100`, bump the
feed stream's flow rate, advance to `t=200`, and note the visible kink in
the concentration chart at `t=100` where the tweak took effect. Then
rewind to `t=100` and advance to `t=200` again without editing anything,
showing the chart past `t=100` revert to the un-tweaked trajectory —
demonstrating that rewind genuinely discarded the tweaked branch rather
than merely hiding it.
