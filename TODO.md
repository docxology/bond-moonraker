# TODO — moonraker (mission DRAX)

Phase-2 build record for the `PROJECT BOND` moonraker package. This file lists
what is built and any declared integration points.

## Built (phase 2)

### Pure domain core (`src/moonraker/`, infrastructure-free + importable without bond-api)

- **shuttle_ops.py** — space-shuttle hijack timeline as a Critical Path Method
  network. `TimelineActivity`, `compute_timeline` (forward/backward pass plus
  cycle detection), `timeline_feasibility` (deadline margin), and the canonical
  `DRAX_HIJACK_TIMELINE` (8 phases, total 57.0 min, feasible within 60 min).
- **orbital_logistics.py** — Drax station orbital logistics. `orbital_period`
  (Kepler), `circular_speed`, `orbits_per_day`, `visibility_half_angle`,
  `pass_duration`, `launch_windows`, and the consumables model
  (`consumables_days`, `depletion_day`, `sustainable_crew`,
  `resupply_interval`).
- **centrifuge.py** — centrifuge g-force training profiles. `g_from_rpm` /
  `rpm_for_g`, `max_sustained_duration` (g-tolerance envelope),
  `build_training_profile` (ramp/sustain/decay), `profile_is_safe`.
- **orbital_transfer.py** (phase-4) — Hohmann transfer (`hohmann_transfer`),
  vis-viva (`vis_viva`), phase-wait rendezvous timing (`phase_wait_time`),
  rocket equation (`tsiolkovsky_mass_ratio` / `propellant_fraction` /
  `propellant_mass`) and deorbit burn (`deorbit_dv`).
- **rendezvous.py** (phase-4) — Clohessy–Wiltshire relative-motion guidance:
  `cw_state_transition`, `cw_propagate`, and closed-form
  `single_impulse_intercept` (raises on singular geometry).
- **centrifuge_training.py** (phase-4) — training regimen: g·s exposure
  (`exposure_g_seconds` / `profile_exposure`), GOR tolerance scaling
  (`gor_tolerance_multiplier`), and exposure-capped weekly planning
  (`max_sessions_for_cap` / `plan_training_cycle`).
- **schedule_crashing.py** (phase-4) — minimum-cost time-cost crashing of the
  hijack timeline (`crash_schedule`) with the canonical `DRAX_CRASH_OPTIONS`.

### Protocol adapter

- **mission.py** — implements the frozen BOND-API `MissionProvider`
  (`brief`/`recon`/`plan`/`execute`/`debrief`), slug `moonraker`, codename
  `DRAX`, fixed seed 23, stable SHA-256 `input_hash`; registers real domain
  functions as gadgets with `bond_api.registry.GadgetRegistry`.
- **mission_results.py** — canonical deterministic result computation feeding
  the manuscripts and the `execute`/`run_mission` CLIs.

### Manuscript, variables, figures

- **manuscript_variables.py** — `{{TOKEN}}` hydration from
  `manuscript/config.yaml` + `mission_results`; `save_variables`,
  `write_resolved_manuscript_tree` (no infrastructure dependency).
- **figures.py** — three deterministic matplotlib figures
  (`timeline_critical_path.png`, `orbit_period_windows.png`,
  `centrifuge_g_profile.png`).
- **manuscript/** — tokenised DRAX sections (`00_abstract` … `99_references`).

### Scripts (`scripts/`, thin)

`brief.py`, `recon.py`, `plan.py`, `execute.py`, `debrief.py` (one CLI per
mission phase), `run_mission.py` (flagship: full flow + regenerable artifacts
under `output/`), `z_generate_manuscript_variables.py`.

### Tests (`tests/`, zero mocks, deterministic)

`test_shuttle_ops.py`, `test_orbital_logistics.py`, `test_centrifuge.py`,
`test_orbital_transfer.py`, `test_rendezvous.py`, `test_centrifuge_training.py`,
`test_schedule_crashing.py`, `test_mission.py` (protocol + discovery +
gadgets), `test_mission_results.py`, `test_manuscript_variables.py` (incl. live
`{{TOKEN}}` cross-reference), `test_figures.py`, `test_scripts_smoke.py`.

## Gates

- `pytest --cov=src --cov-fail-under=90`: **164 passed, 99.20% line+branch**.
- `ruff check` + `ruff format`: clean.
- `mypy src/ scripts/`: clean.
- Lineage `template[_]code_project` in prose: zero.
- Git status clean after the path-scoped commit.

## Declared integration points

- **bond-api** (done, phase 1): local path dependency; `mission.py` adapts the
  frozen protocol. Discovery: `bond_api.discovery.load_provider("moonraker")`
  imports `moonraker.mission` → `MissionProvider`.
- **bond-utilities provenance** (not yet converted in moonraker): if the suite
  later standardises on `bond_utilities.mission_io.record_provenance_outcome`,
  `mission.py execute()` should delegate its `Provenance` record through it.
  Acceptance: no signature change to `MissionOutcome`.
- **bond-coordinator / bond-orchestrator**: consume the provider by slug via
  `bond_api.discovery` + `MissionRegistry`; moonraker needs no changes.

## Notes

- `output/` is git-ignored (regenerable); `scripts/run_mission.py` restores a
  byte-identical tree on re-run (determinism proof).
- "tech-debt-free" gate: all tracked files free of empty/stub/mock markers.
