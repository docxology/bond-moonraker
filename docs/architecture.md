# Architecture — moonraker (mission DRAX)

How the package is put together, module by module. Every file named here exists;
if you add or remove one, update this file in the same commit.

## Layers

Dependencies point strictly downward. Nothing below ever imports something above.

| Layer | Modules | May import |
|---|---|---|
| **L0 · Domain core** | `shuttle_ops`, `schedule_crashing`, `orbital_logistics`, `orbital_transfer`, `rendezvous`, `centrifuge`, `centrifuge_training` | stdlib only (`math`, `dataclasses`) — plus, within the layer, each other |
| **L1 · Composition** | `mission_results` | L0 |
| **L2 · Presentation** | `manuscript_variables`, `figures` | L1, L0, `yaml`, `matplotlib` |
| **L3 · Protocol adapter** | `mission` | `bond_api`, L1, L0 |
| **L4 · Orchestrators** | `scripts/*.py` | anything in `src/`; no logic of their own |

Two invariants make this worth stating:

1. **`mission.py` is the only module that imports `bond_api`.** Remove
   `bond-api` from the environment and the entire domain core, the manuscript
   variables and the figures still import and still compute. That is what makes
   the science liftable out of the suite.
2. **No module under `src/moonraker/` imports `infrastructure.*`.** This package
   is standalone by contract (`STANDALONE.md`), not a template subdirectory.

## The domain core, module by module

### `shuttle_ops.py` — the hijack as a project network

`TimelineActivity` (name, duration, prerequisites) and `TimelineSchedule` (the
solved early/late starts and finishes, slack, total duration, critical path).
`compute_timeline` runs the Critical Path Method: validate → forward pass
(ES = max EF of prerequisites) → backward pass (LF = min LS of successors) →
slack → the zero-slack chain. Validation is not decorative: duplicate names,
prerequisites naming activities that do not exist, and dependency cycles are all
rejected (Kahn-style strip) before any arithmetic runs.
`timeline_feasibility` returns `(feasible, margin_min)` against the shuttle's
point of no return. `DRAX_HIJACK_TIMELINE` is the canonical eight-phase network.

### `schedule_crashing.py` — buying the deadline down

`CrashableActivity` adds a crash duration and a linear cost per minute to each
phase. `crash_schedule` re-solves the CPM after every step, picks the cheapest
still-crashable activity **on the current critical path**, and crashes it one
minute at a time — re-solving each round because compressing one path can hand
criticality to another. It returns a `CrashResult` carrying the original and
final durations, the total cost, the per-activity minutes bought, the final
critical path, and a `feasible` flag that is False when even a fully-crashed
network cannot reach the deadline. `DRAX_CRASH_OPTIONS` mirrors the canonical
timeline with crash economics attached.

### `orbital_logistics.py` — the station's orbit and stores

Physical constants (`EARTH_RADIUS_KM`, `EARTH_MU_KM3_S2`, `SIDEREAL_DAY_S`) and
two families of function. *Orbit*: `orbital_period` (Kepler's third law),
`circular_speed`, `orbits_per_day`, `visibility_half_angle` and `pass_duration`
(horizon geometry with a documented linear elevation-threshold shrinkage), and
`launch_windows`, which emits a deterministic `LaunchWindow` series at each
half-period plane crossing. *Stores*: `consumables_days`, `depletion_day`,
`sustainable_crew` (the floored crew a given cadence supports) and
`resupply_interval`. This module also supplies the constants the transfer and
rendezvous modules reuse — the only intra-L0 dependency worth knowing.

### `orbital_transfer.py` — flying the resupply

`vis_viva` underpins everything. `hohmann_transfer` returns a `HohmannTransfer`
with both burns, the total Δv, the half-ellipse time and the transfer
semi-major axis, refusing coincident or sub-surface orbits. `phase_wait_time`
computes the Hohmann lead angle and how long a chaser in the lower orbit waits
for it — it requires the chaser to actually be lower, since the catch-up rate
would otherwise have the wrong sign. `tsiolkovsky_mass_ratio`,
`propellant_fraction` and `propellant_mass` size the tanks; `deorbit_dv` is the
retrograde burn that drops perigee into the atmosphere.

### `rendezvous.py` — the last few kilometres

Linearised Clohessy–Wiltshire relative motion in the station's LVLH frame.
`mean_motion` for the reference orbit, `cw_state_transition` for the 6×6 STM,
`cw_propagate` to push a relative state forward, and `single_impulse_intercept`,
which solves the 2×2 in-plane system plus the decoupled cross-track channel in
closed form for the impulse that zeroes relative position at a chosen time. It
**raises** at the geometric singularities (whole-period intercept times, in-plane
degeneracies) rather than returning a large or wrong number — a chaser there
needs a multi-burn strategy, and the model says so instead of pretending.

### `centrifuge.py` — one training run

`g_from_rpm` / `rpm_for_g` are the centripetal physics.
`max_sustained_duration` is the +Gz tolerance envelope, a documented power-law
fit `t = min(800·g^-2.5, 60)`. `build_training_profile` discretises a
ramp → sustain → decay run into a `TrainingProfile`. `profile_is_safe`
adjudicates the plateau against **two independent ceilings** and reports the
tighter as `allowable_s`: the derated tolerance envelope (physiological) and
`duration_limit_s` (procedural). A separate peak-g ceiling rejects outright.
Both duration ceilings are exercised by tests — which matters, because a
validated-but-unused limit argument was a real defect here once.

### `centrifuge_training.py` — the weekly regimen

`gor_tolerance_multiplier` scales tolerance with gradual onset rate (slower
onset → more tolerated time), clamped to a documented band.
`exposure_g_seconds` and `profile_exposure` dose a run in g·s above baseline,
deriving the sampling step from the profile's own time samples.
`max_sessions_for_cap` and `plan_training_cycle` return a `TrainingCycle`
carrying the planned and recommended session counts and a `feasible` flag that
requires **both** the per-session daily cap and the cumulative weekly cap.

## Composition and presentation

`mission_results.py` holds `MISSION_DEFAULTS` (mirroring
`manuscript/config.yaml` → `mission:`) and the factories `compute_transfer`,
`compute_rendezvous`, `compute_training`, `compute_crash`, with
`compute_mission_results` returning the flat, token-keyed result dict. It is the
**single canonical computation**: the mission adapter, the manuscript variables
and the CLIs all read it, which is why an outcome value and its manuscript token
cannot disagree. If you find yourself recomputing a metric anywhere else, that
is the bug.

`manuscript_variables.py` merges config identity + the `mission:` block +
computed results into the token map, writes it as JSON, and resolves
`manuscript/[0-9]*.md` into `output/manuscript/`. Guide files are deliberately
not resolved, so their literal token examples cannot leak into rendered prose.

`figures.py` renders five deterministic PNGs through the headless `Agg` backend:
`timeline_critical_path`, `orbit_period_windows`, `centrifuge_g_profile`,
`hohmann_transfer`, `training_weekly_load`.

## How `mission.py` implements the frozen `MissionProvider`

`bond-api` defines a runtime-checkable `MissionProvider` protocol. Its shape is
**frozen** across the suite: `bond-cli`, the coordinator's reconcile and the
orchestrator all consume it by name, so changing a method signature or the
module-level export names breaks packages that are not this one.

What moonraker exposes at module top level, and what each piece is for:

| Export | Role |
|---|---|
| `MissionProvider` | The class itself — discovery imports `<slug>.mission` and reads this attribute |
| `PROVIDER` | A singleton instance for scripts and the orchestrator |
| `provider()` | Factory returning a fresh instance |
| `GADGETS` | Module-level `GadgetRegistry`, populated at import by `_register_gadgets()` |
| `FILM`, `CODENAME` | `"moonraker"`, `"DRAX"` |

The five lifecycle stages:

1. **`brief() -> MissionBrief`** — declares six objectives (one per concept area
   plus the deepened ones), six `Asset` manifests naming the source module for
   each, and two `Constraint` records (determinism, integrity).
2. **`recon(ReconRequest) -> ReconReport`** — returns a deterministic `Finding`
   per capability, echoing the request goal as the first finding.
3. **`plan(MissionBrief) -> MissionPlan`** — six `Step`s, each with an `action`
   string and a params dict: `critical_path`, `launch_windows`, `g_profile`,
   `hohmann_transfer`, `training_cycle`, `schedule_crash`.
4. **`execute(MissionPlan) -> MissionOutcome`** — dispatches on `step.action`.
   Every branch resolves its inputs as `{**MISSION_DEFAULTS, **step.params}`, so
   a plan that varies a parameter varies the whole computation rather than only
   the part that happens to read it. An **unknown action raises `ValueError`**;
   silently skipping it would inflate `steps_completed` and report a success
   that was never computed. Provenance carries the package version, the seed,
   `wall_time_s=0.0` and a stable SHA-256 `input_hash` over the serialized plan.
5. **`debrief(MissionOutcome) -> Debrief`** — the standing DRAX lessons plus
   values pulled from the outcome.

The provider holds no state. Two `execute` calls on equal plans return equal
results and an identical `input_hash`; `tests/test_mission.py` asserts exactly
that, along with protocol conformance via `isinstance` against the
runtime-checkable protocol and discovery by slug through `bond_api.discovery`.

**Deepen inside, never at the seam.** New domain modules, richer internals and
more gadgets are all fine. Renaming a stage, changing a return type or dropping
a module-level export is not.

## Data flow, end to end

```
manuscript/config.yaml (mission:)
        │
        ▼
mission_results.compute_mission_results()  ← MISSION_DEFAULTS fallback
        │
        ├─► mission.MissionProvider.execute()  ─► MissionOutcome + Provenance
        ├─► manuscript_variables.generate_variables() ─► token map
        │            └─► write_resolved_manuscript_tree() ─► output/manuscript/
        └─► figures.render_*()                 ─► output/figures/*.png
```

`scripts/run_mission.py` walks the whole diagram in one command; the per-phase
CLIs (`brief`, `recon`, `plan`, `execute`, `debrief`) each drive one stage.
