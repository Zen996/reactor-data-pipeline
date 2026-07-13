# CSTR Simulation GUI

Streamlit-based interactive front-end for the configurable dynamic
simulation engine.  Configure a stirred-tank reactor, run it forward in
time, tweak parameters live, rewind to a checkpoint, and export data.

```bash
streamlit run app/app.py
```

---

## Sidebar: Configuration Form

Fill in this form and click **Build Experiment** to start.

### Species

Each species is a chemical that exists in the reactor.  Define its name,
phase (liquid/vapor), and **initial quantity** (how much is in the tank
at time 0).  Set initial quantity to 0 if the species is fed in by a
stream rather than being pre-loaded.

### Streams

A stream is a pipe feeding material into the reactor.  Each stream has:

| Field | Meaning |
|---|---|
| **Name** | Label for the stream (appears in charts and exported data) |
| **Phase** | Whether this stream injects liquid or vapor |
| **Flow signal** | Time-varying function for the volumetric flow rate of this stream (see Signals below) |
| **Composition** | For each species in the stream, a signal giving its concentration in the feed (see Signals below). The species must be declared in the Species section above. |
| **Active** | Uncheck to disable the stream without removing it |

The actual inflow of a species at any time is:
```
inflow_rate = flow_signal(t) × composition_signal(t)
```

> **Composition values are absolute concentrations**, not fractions.
> They are in the same arbitrary units as the reactor state (e.g. mol/L
> or kg/m³).  They do **not** need to sum to 1.0 — each species gets
> its own independent concentration signal.  If you want fractional
> feed, set each species' concentration to your desired fraction and
> ensure they are dimensionally consistent.
>
> **Composition and flow signal are different physical dimensions.**
> The flow signal is a volumetric rate (e.g. L/s), while composition is
> concentration (e.g. mol/L).  Their numerical values are not directly
> comparable — a composition of 2.0 with a flow of 0.5 simply gives an
> inflow rate of 1.0 mol/s.

### Signals

Both flow rates and composition concentrations are defined by **signals**
— time-varying functions chosen from a dropdown:

| Signal type | Parameters | Behaviour |
|---|---|---|
| `constant` | Value | Always returns the same number |
| `step` | Baseline, Step value, Step time | Returns `baseline` before step_time, then `step_value` after |
| `ramp` | Start value, Slope, Start time, Max, Min | Linear increase from `start_value` at `start_time` at rate `slope`. Optional cap at `max_value` / `min_value`. |
| `sinusoid` | Amplitude, Frequency, Offset | `offset + amplitude × sin(2π × freq × t)` |
| `square` | Amplitude, Frequency, Duty cycle, Offset | Square wave alternating between offset+amplitude and offset-amplitude. `duty_cycle` fraction of the period spent at the high value. |
| `triangle` | Amplitude, Frequency, Offset | Symmetric triangle wave |
| `gaussian_noise` | Mean, Std | Random value drawn from a normal distribution (each time step gives a different value). **Seed** on the Simulation section controls reproducibility. |
| `uniform_noise` | Low, High | Random value drawn from a uniform distribution |

> Composition signals for streams currently support only deterministic
> signal types (constant, step, ramp, sinusoid, square, triangle).
> Noise types are available for the flow signal and for Sensors.

### Reactions

First-order or elementary (stoichiometric-order) reactions.  Format
reactants and products as comma-separated `Species:Coefficient` pairs:

```
A:1,B:2    →     C:1,D:2
```

The rate constant `k` controls reaction speed.  The reaction rate is:

```
rate = k × [A]^order_A × [B]^order_B × ...
```

where `[X]` is the **concentration** of species X (`liquid.X / volume`).
The per-step change in absolute quantity is `coeff × rate × dt × volume`,
so `k` has units of `(concentration)^(1-n) / time` for an n-th-order
reaction (e.g. `1/s` for first order, `L/(mol·s)` for second order).

Reaction rate is clamped so no reactant goes negative.  All reactions
are **liquid-phase only** (see `KNOWN_ISSUES.md`).

### Decays

First-order decay: a species disappears at rate `k × [species]`, optionally
producing other species.  Example: species `A` decays with k=0.1, producing
`B:1` (one unit of B per unit of A decayed).  Phase can be liquid or vapor.

### Equilibria

Liquid/vapour phase equilibrium for a single species.  Net transfer
between phases:

```
net = evaporation_coeff × [species]_liquid
    − condensation_coeff × [species]_vapor
```

A positive `net` means material moves from liquid to vapour.  The process
auto-registers the species in both phases if it only exists in one.

### Sensors

Additive measurement noise.  For each sensor, the true species quantity in
the chosen phase is read, a noise value is drawn from the noise signal, and
the sum is written to an output column.

- **Noise type**: Gaussian (mean ± std) or Uniform (low–high range)
- **Output key**: The column name under which the noisy reading appears
  in the exported data (e.g. `sensor_0` appears as `derived.sensor_0`)

Sensors **never modify** the physical state — they only add derived readings.

### Reactor

| Field | Meaning |
|---|---|
| **Outflow mode** | `constant_volume` (outflow = inflow, level constant), `fixed` (constant outflow rate), or `signal` (time-varying outflow defined as a signal) |
| **dt** | Timestep in seconds.  Smaller = more accurate but more steps. |
| **Duration** | Total simulation time in seconds |
| **Seed** | RNG seed for reproducible stochastic runs (noise signals).  Set to 0 for non-deterministic runs. |
| **Max volume** | Initial reactor volume (litres / arbitrary units consistent with your species quantities). The reactor starts at this volume. |
| **Min volume** | Outflow is **disabled** while `volume ≤ min_volume`. The tank must fill above this level before the outlet opens. Set to 0 (default) for immediate outflow. |

---

## Main Panel

Once the experiment is built, the sidebar switches to show restart/edit
buttons and download controls.  The main panel has two columns:

### Left column — Run Controls + Live Parameters

#### Run Controls

| Button | What it does |
|---|---|
| **Step once (▶)** | Execute exactly one timestep (`dt`) forward |
| **Advance (▶▶)** | Run repeatedly until the target time (entered in the "Run to time" box) |
| **Rewind (⏮)** | Revert the simulation state, recorder, and manipulation firing history to the nearest checkpoint at or before the "Rewind target time". **Live parameter edits are preserved.** |
| **Reset** | Clear everything and return to the configuration form |

A warning banner appears if any signal uses noise, since continuing from
a rewind will not reproduce the original trajectory.

#### Live Parameters

Editable sections (click to expand):

- **Streams**: Toggle active/inactive, change flow rate or composition
  signals.  Edits take effect on the **next** step — no rebuild needed.
- **Reactions**: Change rate constants on the fly.
- **Manipulations**: View one-shot status and firing time (read-only in
  the GUI; see "Manipulations" note below).

> **Manipulations** (time-triggered, threshold-triggered, or periodic
> actions like injecting species or draining the reactor) are configured
> via YAML/JSON config files or programmatic API, not through the GUI
> form.  They appear in Live Parameters for monitoring.

### Right column — Charts

#### Input Streams

One line per stream showing its flow rate over time.  Checkboxes let you
show/hide individual streams.

#### Outlet

One line per species showing its **outlet mass flow rate** over time
(`derived.outlet.<species>`), plus a **total** line summing all species.
Checkboxes let you show/hide individual species.  This is a **rate**
(mass/time or moles/time), not a quantity — compare with the `liquid.*`
inventory in the reactor section.

#### Reactor

Multi-select any combination of columns to plot:

- `liquid.<species>` — **Quantity** (mass or moles) of that species
  currently in the reactor's liquid phase at that instant
- `conc.<species>` — **Absolute concentration** of that species
  (`liquid.<species> / volume`).  Same unit as your composition signals.
  These are **not** normalized fractions — they will not sum to 1 unless
  your total mass/volume ratio happens to be 1.  The sum of all
  `conc.*` values equals `total_mass / volume`.
- `vapor.<species>` — Same as `liquid.*` for the vapour phase
- `derived.stream.<name>.flow_rate` — Same as the input-stream chart
- `derived.stream.<name>.inflow.<species>` — Inflow rate of a species
  from a specific stream (flow × composition)
- `derived.reaction_rate_<i>` — Extent per unit time for reaction *i*
  (units: concentration / second). This is `extent / dt` where extent
  is the change in reaction progress in concentration units per step.
- `derived.decay_rate_<species>` — First-order decay rate for a species
  (units: concentration / second)
- `derived.equilibrium_net_<species>` — Net phase transfer rate for a
  species.  Positive = liquid → vapour; negative = vapour → liquid.
- `derived.<output_key>` — Noisy sensor readings (one column per sensor)

---

## Understanding Derived Columns

All output columns starting with `derived.` are **snapshot quantities**
computed during each timestep for monitoring and analysis.  They do
**not** represent physical state — the physical state lives in
`liquid.*` and `vapor.*`.

| Column pattern | Source | Meaning |
|---|---|---|
| `derived.stream.<name>.flow_rate` | MixingProcess | Volumetric flow rate of a feed stream |
| `derived.stream.<name>.inflow.<species>` | MixingProcess | Inflow rate of a species via a feed stream |
| `derived.outlet.<species>` | MixingProcess | **Outlet mass flow rate** (mass/time or moles/time). `outflow_rate × liquid_qty / volume`. This is a **rate**, distinct from `liquid.<species>` which is the tank inventory. |
| `derived.outlet.total` | MixingProcess | Sum of all species outlet rates. Total mass (or moles) leaving the reactor per unit time. |
| `derived.reaction_rate_<i>` | ReactionProcess | Reaction progress per unit time (conc/s) |
| `derived.decay_rate_<species>` | DecayProcess | Decay rate (conc/s), first-order |
| `derived.equilibrium_net_<species>` | EquilibriumProcess | Net liquid→vapour transfer rate (conc/s) |
| `derived.<custom_key>` | SensorNoiseProcess | Noisy sensor reading |

---

## Export

Download the current recorded data at any time via the sidebar buttons:

- **CSV** — Universally readable, opens in Excel or any text editor
- **Parquet** — Columnar binary format, faster to load in pandas

If you rewind, any data past the rewind point is truncated from the
export.

---

## Typical Workflow

1. Open the app → fill in the configuration form
2. Click **Build Experiment**
3. Click **Advance** a few times to run 5–10 seconds of simulation
4. Observe the charts — open "Live Parameters" expanders and tweak
   a stream flow or reaction rate
5. Click **Advance** again to see the effect
6. Enter a rewind target time and click **Rewind** to go back to a
   previous state, then advance again with different live params
7. Download CSV or Parquet for offline analysis
