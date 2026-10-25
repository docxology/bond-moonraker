# TODO — moonraker (mission DRAX)

`moonraker` is the `PROJECT BOND` suite package for *Moonraker* (1979, mission
codename **DRAX**). Seven pure stdlib domain modules (CPM scheduling, time-cost
crashing, Kepler logistics, Hohmann transfer, Clohessy–Wiltshire rendezvous,
+Gz centrifuge adjudication, exposure-capped training) are composed by one
canonical computation (`mission_results.py`) that feeds the manuscript tokens,
the figures and the frozen BOND-API `MissionProvider` adapter. Test counts and
coverage live in `docs/_generated/COUNTS.md` and are not restated here;
`ruff check`, `ruff format --check` and `mypy src/ scripts/` are clean, and
`tests/` uses zero mocks. What is already built is described in `README.md`,
`docs/architecture.md` and the manuscript — this file does not duplicate them.

## Open work

**Round-2 status (2026-08-06): C1, C2, C3, V1, D1 and D2 below are closed.**
Their write-ups are kept as the defect record; see *Round-2* at the foot of this
file for each fix and its regression evidence. E1–E5 and the *Known limitations*
list are still open.

### Correctness

**C1 — `execute()`'s `launch_windows` branch silently ignores the canonical
orbit parameters.** The branch at `src/moonraker/mission.py:252-271` reads the
short keys `altitude_km` and `num_windows` from `step.params`, while
`MISSION_DEFAULTS` (merged in as `{**MISSION_DEFAULTS, **step.params}`) names
them `station_altitude_km` and `launch_horizon_h`. A step that sets the
canonical name is accepted and discarded. Reproduced today:

```python
Step(action="launch_windows", params={"station_altitude_km": 700.0,
                                      "altitude_km": 350.0, "num_windows": 6})
# -> results["orbit"]["period_s"] == 5483.55  (the 350 km value; 700 km ignored)
```

The branch also has no horizon concept at all: it returns exactly
`num_windows` entries, which is the input-echo pattern that was removed from
the published path (`compute_orbit` uses `windows_in_horizon`,
`src/moonraker/mission_results.py:116-117`). The plan step that feeds it still
hardcodes `{"altitude_km": 350.0, "num_windows": 6}` at
`src/moonraker/mission.py:169-171`.
**Done when** the branch resolves its inputs through `compute_orbit(params)`
(or reads the canonical key names), and a test asserts that a step setting
`station_altitude_km=700.0` moves `results["orbit"]["period_s"]` off the 350 km
value. Note the plan's step param keys are part of what `bond-cli` and the
coordinator serialize — check `../bond-cli` and `../bond-coordinator` before
renaming them, and prefer accepting both spellings over a silent drop.
**Command:** `uv run pytest tests/test_mission.py -q`

**C2 — `execute()`'s `g_profile` branch cannot express
`centrifuge_margin_fraction`, so its verdict is computed under a different rule
than the published one.** `src/moonraker/mission.py:281-285` calls
`profile_is_safe(profile, g_limit=..., duration_limit_s=...)` and never passes
`margin_fraction`, so it always uses the function default `0.2`
(`src/moonraker/centrifuge.py:166`). `compute_centrifuge` passes the configured
value (`src/moonraker/mission_results.py:147-151`). They agree today only
because `manuscript/config.yaml:64` also says `0.2`. Reproduced today:

```python
Step(action="g_profile", params={"target_g": 6.0, "radius_m": 8.0,
                                 "sustain_s": 12.0,
                                 "centrifuge_margin_fraction": 0.5})
# -> results["centrifuge"]["allowable_s"] == 7.2577  (unchanged; 0.5 ignored)
```

**Done when** the branch's `allowable_s` moves when a step sets
`centrifuge_margin_fraction`, pinned by a test that flips it and asserts the
adapter's `allowable_s` equals `compute_centrifuge`'s under the same value.
**Command:** `uv run pytest tests/test_mission.py -q`

**C3 — `numpy` is a declared runtime dependency with no importer.**
`pyproject.toml:20` requires `numpy>=1.24.0`;
`grep -rn "import numpy" src/ scripts/ tests/` returns nothing (matplotlib
pulls it transitively). **Done when** either the dependency is removed from
`pyproject.toml` and the suite still passes after a re-sync, or a module
actually imports it.
**Command:** `uv sync --all-extras && uv run pytest tests/ --cov=src --cov-fail-under=90 -q`

### Verification

**V1 — the strict-mode guard's fall-through is the one uncovered branch in the
package.** `src/moonraker/manuscript_variables.py:65->73`: no unit test calls
`build_variable_map(..., require_analysis_outputs=True)` with
`output/data/mission_results.json` present, so the "strict mode is satisfied
and proceeds" path is exercised only through the subprocess smoke test
(`tests/test_scripts_smoke.py:74-81`), which coverage does not see. The
negative control exists (`:83-93`, strict mode refusing in `tmp_path`); the
positive control does not. **Done when** a unit test builds a `tmp_path` tree
containing a real `mission_results.json` plus `manuscript/config.yaml`, calls
the function in strict mode, asserts it returns a map, and coverage on
`manuscript_variables.py` reads 100.00%.
**Command:** `uv run pytest tests/test_manuscript_variables.py --cov=src/moonraker/manuscript_variables.py --cov-report=term-missing -q`

~~**V2 — the byte-identical re-run claim is asserted in prose but by no test.**~~
**DONE 2026-08-05.** The claim was not merely unbound, it was **false**:
`manuscript_variables.py` hydrated `GENERATION_TIMESTAMP` from
`datetime.now(timezone.utc)` at minute resolution and rendered it into
`00_abstract.md` and `manuscript_variables.json`, so two regenerations one
minute apart produced different bytes (reproduced: `5565e1d7…` → `6620ea5f…`
over the `output/` `*.json` + `*.md` set). The single test guarding determinism
injected a fixed `now` into both calls and so could never fail on it.
Resolution: the wall clock was removed from the persisted path entirely. The
token is now `MANUSCRIPT_DATE`, read from the committed `paper.date` in
`manuscript/config.yaml`; `generate_variables()` no longer accepts a `now`
argument. `tests/test_regeneration_determinism.py` binds the claim two ways —
a full double regeneration into an isolated tree with a SHA-256 compare of
every file, and an AST parse of `src/moonraker/` + `scripts/` for wall-clock
calls carrying a positive control and a non-empty-scan-set assertion. Four
tests were confirmed to go red when the `datetime.now()` was temporarily
reintroduced. The prose in `manuscript/06_reproducibility.md`, `AGENTS.md`,
`docs/testing_philosophy.md`, `scripts/CONVENTIONS.md` and
`scripts/run_mission.py` now states the guarantee with its exact scope:
`PYTHON_VERSION` and `PLATFORM` are the only environment-derived values, so
byte-identity holds per interpreter and platform.
**Command:** `uv run pytest tests/test_regeneration_determinism.py -q`

### Documentation

**D1 — `docs/architecture.md` claims a data flow that two of six `execute`
branches do not follow.** The diagram at `docs/architecture.md:217` hangs
`mission.MissionProvider.execute()` off the `mission_results` factories node,
and `:184-186` states "Every branch resolves its inputs as
`{**MISSION_DEFAULTS, **step.params}`, so a plan that varies a parameter varies
the whole computation rather than only the part that happens to read it." The
`launch_windows` and `g_profile` branches call `orbital_logistics` and
`centrifuge` directly and drop canonical keys (see C1, C2) — the merge happens,
the branch does not read the merged keys. **Done when** C1 and C2 are fixed and
the diagram is true as drawn, or — if the adapter's plan-parameterised path is
kept deliberately separate — the diagram and the `:184-186` sentence say so
explicitly and name which branches bypass the factories.
**Command:** `grep -n "Every branch resolves" -A 3 docs/architecture.md` and
re-read `src/moonraker/mission.py:240-296` against it.

**D2 — `ORBIT_SUSTAINABLE_CREW` publishes 450 for a station the same config
crews at 6, with no scale note.** `sustainable_crew(5400 kg, 6 d, 2 kg/p/d)`
= 450 is arithmetically exact (it is capacity per resupply cycle divided by
per-capita consumption), but the prose reads as an operational claim: "sustain
**450** crew" at `manuscript/03_results.md:43`, `manuscript/00_abstract.md:19`
and `manuscript/04_conclusion.md:15`, against `crew: 6` at
`manuscript/config.yaml:53`. Nothing in the manuscript reconciles the two, and
`ORBIT_CONSUMABLES_DAYS` is coincidentally also 450 (450 days for 6 crew),
which makes the pair easy to misread as one number. This was flagged by the
adversarial audit as out of that pass's scope. **Done when** the results
paragraph states what the 450 means (a logistics ceiling per resupply cycle,
not a habitability figure) and distinguishes it from the 450-day stores
figure — or a token carries the ratio explicitly.
**Command:** `uv run python scripts/run_mission.py && uv run python scripts/z_generate_manuscript_variables.py`
then read `output/manuscript/03_results.md`.

### Extension

**E1 — decide `gor_tolerance_multiplier`: wire it in or delete it.**
`src/moonraker/centrifuge_training.py:38` is implemented, exported and tested
(15 assertions in `tests/test_centrifuge_training.py`) with **zero** call sites
outside its own `__all__` entry. The audit's finding was resolved by *stating*
the limitation, not by making the claim true:
`manuscript/02_methodology.md:103-111` now says it is not part of any reported
number, and `manuscript/07_scope_and_related_work.md:30-32` carries it as a
named non-modelled item. The paper is honest either way; the knob is still a
knob that does nothing. **Done when** either (a) `compute_training` credits the
onset rate, the published training tokens move, and a test pins the new values
against hand arithmetic, or (b) the function, its tests, its `__all__` entry
and both manuscript caveats are removed together.
**Command:** `uv run pytest tests/test_centrifuge_training.py tests/test_mission_results.py -q`

**E2 — multi-burn rendezvous.** `single_impulse_intercept`
(`src/moonraker/rendezvous.py:126`, raising at `:166` and `:168`) has no answer
at the geometric singularities — whole-period intercept times and in-plane
degeneracies — because no single impulse exists there. A two-burn
Lambert-style solver would return a Δv instead of an exception. **Done when**
each singular case in `tests/test_rendezvous.py` gains a companion assertion
that the multi-burn path returns a finite Δv verified against an independent
hand calculation.
**Command:** `uv run pytest tests/test_rendezvous.py -q`

**E3 — stochastic activity durations.** The hijack network is deterministic
CPM, so `SHUTTLE_TOTAL_MIN` (57.0) has no confidence interval; this is
currently carried as a stated scope boundary
(`manuscript/07_scope_and_related_work.md:27-29`). A PERT three-point estimate
per activity in `src/moonraker/shuttle_ops.py` would give one. **Done when** a
new token reports the interval, the deterministic total is unchanged as the
mean case, and the scope bullet is retired.
**Command:** `uv run pytest tests/test_shuttle_ops.py tests/test_mission_results.py -q`

**E4 — centrifuge remediation as a computed recommendation.**
`manuscript/03_results.md:84-86` states the plateau that *would* pass by pointing
the reader at `{{CENTRIFUGE_ALLOWABLE_S}}` and letting them infer the fix. A
dedicated `compute_*` factory in `mission_results.py` returning a
certified-by-construction profile (shortened plateau, or reduced peak) would
make the recommendation a first-class result. **Done when** a new token carries
the remediated profile and a test asserts `profile_is_safe` returns `True` for
it under the shipped config.
**Command:** `uv run pytest tests/test_mission_results.py -q`

**E5 — `bond-utilities` provenance delegation.**
`../bond-utilities/src/bond_utilities/mission_io.py:153` provides
`record_provenance_outcome`. `moonraker` does not depend on `bond-utilities`
(`pyproject.toml:19-24` lists only `numpy`, `matplotlib`, `pyyaml`,
`bond-api`), and `mission.py` builds its `Provenance` record inline. If the
suite standardises on the shared helper, `execute()` should delegate through
it. **Done when** the dependency is added, the record is delegated, and:
no signature change to `MissionOutcome`, `wall_time_s` still `0.0`, and
`input_hash` unchanged for an unchanged plan.
**Command:** `uv run pytest tests/test_mission.py -q`

## Known limitations (not bugs)

- **Ideal two-body orbits.** No drag, no J2, no third-body, no solar radiation
  pressure, so the launch-window series never precesses and the station never
  decays. Stated at `manuscript/07_scope_and_related_work.md:14-16`. Adding a
  decay term would make the resupply cadence time-dependent and is a different
  paper; the closed-form, hand-auditable model is the deliberate choice.
- **Scalar +Gz, no biodynamics.** `centrifuge` treats tolerance as a
  population-average envelope with no individual variation, no anti-G straining
  manoeuvre, no G-suit and no inter-session fatigue
  (`manuscript/07_scope_and_related_work.md:23-26`).
- **No ascent or re-entry trajectories.** The timeline ends at docking; the
  deorbit burn is sized but not flown
  (`manuscript/07_scope_and_related_work.md:12-13`).
- **Onset-rate credit is not in any published number.** This is the audit-forced
  softening: rather than wiring `gor_tolerance_multiplier` in (which would move
  published values), the claim was narrowed. The honest scope today is that the
  reported allowance and session count are onset-rate–**independent**, said
  plainly at `manuscript/02_methodology.md:103-111` and listed as non-modelled
  at `manuscript/07_scope_and_related_work.md:30-32`. The paper is accurate;
  the code carries an unused function. The remaining decision is E1 — do not
  re-litigate the *wording*.
- **The suite writes into the package's real `output/` tree.**
  `tests/test_scripts_smoke.py` invokes the CLIs with `cwd=PROJECT_ROOT`, so
  running the tests regenerates `output/`. Accepted: `output/` is git-ignored
  and fully regenerable, and running the real scripts against the real tree is
  what makes the smoke test a smoke test. The one case where the isolation
  mattered — the strict/draft precondition — was moved to `tmp_path`
  (`tests/test_scripts_smoke.py:83-101`).
- **`ORBIT_WINDOW_COUNT` is 6, the same number the old hardcoded
  `num_windows=6` produced.** This is a coincidence of the shipped 4-hour
  horizon, not a surviving input echo. The filter is real
  (`orbital_logistics.windows_in_horizon`, consumed at
  `mission_results.py:116-117`) and is bound in both directions by
  `tests/test_mission_results.py:219-220`: an 8 h horizon raises the count and
  a 0.05 h horizon drops it. Verified this session — do not re-open on the
  strength of the number alone.
- **Coverage is 99.92%, not 100%.** The single gap is V1 above; every other
  module in `src/moonraker/` measures 100.00% line+branch.

## Verification

Run from the repository root (the working tree must be a sibling of the
`bond-api` checkout, which `[tool.uv.sources]` resolves as `../bond-api`). If `uv` reports
`Failed to initialize cache`, the sandbox is blocking `~/.cache/uv`; re-run
outside it.

```bash
uv sync --all-extras                                     # bare `uv sync` prunes pytest

uv run pytest tests/ --cov=src --cov-fail-under=90 -q    # THE GATE
#  expect: 0 failed, "Required test coverage of 90% reached"
#  (counts and coverage %: docs/_generated/COUNTS.md — not restated here)

uv run ruff check src/ scripts/ tests/                   # expect: All checks passed!
uv run ruff format --check src/ scripts/ tests/          # expect: no reformat needed
uv run mypy src/ scripts/                                # expect: Success: no issues found

grep -rn "MagicMock\|mocker.patch\|unittest.mock" tests/*.py || echo "no mocks: clean"
#  expect: "no mocks: clean" (tests/PATTERNS.md names the banned symbols in prose)

uv run python scripts/run_mission.py                     # regenerates output/ (exit 0)
uv run python scripts/z_generate_manuscript_variables.py # strict; exit 2 without outputs

git status --short                                       # expect: empty (output/ is ignored)
```

`docs/_generated/COUNTS.md` holds the measured counts and is regenerated from
the gate — update it there, and do not quote test counts or coverage anywhere
else in prose.


## Round-2 (2026-08-06)

Round-2 improvement pass: closed the silent-drop defect class in the mission
adapter, removed an unused dependency, pushed `src/` coverage to 100.00%, and
deepened the manuscript (consolidated results table, computed centrifuge
remediation, crew-ceiling honesty).

### Findings and fixes (each with regression evidence)

- **R2-1 (fixes TODO C1) — `execute()`'s `launch_windows` branch silently
  dropped the canonical orbit keys.** It read the short keys `altitude_km` and
  `num_windows` while `MISSION_DEFAULTS`/`config.yaml` name `station_altitude_km`
  and `launch_horizon_h`, so a step setting the canonical name was accepted and
  ignored, and the window count was an input echo rather than a horizon-filtered
  result. **Fix:** the branch now resolves through `compute_orbit(params)` via a
  new `mission._normalise_params` alias layer (`altitude_km → station_altitude_km`,
  etc.), and the plan step uses the canonical keys. Both spellings now move the
  computation. **Evidence:** `tests/test_mission.py::TestCanonicalStepParamsAreHonoured`
  (`test_launch_windows_honours_station_altitude`: `station_altitude_km=700`
  moves `period_s` off 350 km and the `altitude_km` alias does the same;
  `test_launch_windows_reports_horizon_bounded_windows`).

- **R2-2 (fixes TODO C2) — the `g_profile` branch ignored
  `centrifuge_margin_fraction`.** It called `profile_is_safe` without the margin,
  so a step that varied the margin had no effect. **Fix:** the branch now
  resolves through `compute_centrifuge(params)`, which applies the configured
  margin under the same rule as the published result. **Evidence:**
  `test_centrifuge_margin_fraction_honoured_by_g_profile_step` asserts
  `allowable_s` moves with the margin and equals `compute_centrifuge` under the
  same value.

- **R2-3 (sibling defect, same class) — the `schedule_crash` and
  `training_cycle` plan steps named short/non-canonical keys that the factories
  did not read.** `schedule_crash` set `deadline_min` while `compute_crash`
  reads `crash_deadline_min`; `training_cycle` set `sessions_per_week` /
  `daily_cap_g_s` / `weekly_cap_g_s` while `compute_training` reads the
  `training_*` spellings. Both only worked because the defaults coincided.
  **Fix:** plan steps use canonical keys; the alias layer honours both.
  **Evidence:** `test_schedule_crash_honours_canonical_deadline` (a tighter
  `crash_deadline_min` saves more minutes) and
  `test_training_cycle_honours_session_count` (4 vs 2 sessions doubles weekly
  exposure).

- **R2-4 (fixes TODO C3) — `numpy` was a declared dependency with no importer.**
  Removed `numpy>=1.24.0` from `pyproject.toml` (matplotlib supplies it
  transitively); re-synced and the full gate passes. `manuscript/05` now lists
  only the declared deps.

- **R2-5 (fixes TODO V1) — the strict-mode guard's positive branch was the one
  uncovered line in the package.** Added `test_strict_mode_proceeds_when_outputs_exist`
  (`tests/test_manuscript_variables.py`), which builds a `tmp_path` tree with a
  real `mission_results.json`, calls `generate_variables(..., require_analysis_outputs=True)`
  and asserts it returns a map. `manuscript_variables.py` coverage is now
  100.00% line+branch.

- **R2-6 (resolves TODO E4) — centrifuge remediation is now a first-class,
  computed result.** New `mission_results.compute_remediation` factory rebuilds
  the profile with the plateau at the governing allowance and verifies it is
  certified by construction; four `REMEDIATION_*` tokens (`REMEDIATION_SUSTAIN_S`,
  `_SAFE`, `_VERDICT`, `_REDUCTION_S`) join the token map and the consolidated
  results table. **Evidence:** `test_remediation_is_certified_by_construction`
  (`REMEDIATION_VERDICT == "certified"`, `REMEDIATION_SUSTAIN_S ==
  CENTRIFUGE_ALLOWABLE_S`, `REMEDIATION_REDUCTION_S == CENTRIFUGE_EXCEEDANCE_S`).

- **R2-7 (resolves TODO D1) — `docs/architecture.md` now states the real data
  flow.** The `execute()` paragraph documents factory resolution plus the
  `_normalise_params` alias layer, matching the diagram.

- **R2-8 (resolves TODO D2) — the `ORBIT_SUSTAINABLE_CREW` = 450 figure is now
  framed honestly.** The abstract, results and conclusion state it is a
  per-cycle logistics ceiling (`capacity / (cadence × per-capita rate)`), not a
  habitability figure, and distinguish it from the 450-day stores figure and the
  configured crew of 6. A consolidated, token-bound results table was added to
  §Results.

### Gate numbers (2026-08-06)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q   # 256 passed, 0 failed, 0 skipped, 100.00% coverage
uv run ruff check src/ scripts/ tests/                 # All checks passed!
uv run ruff format --check src/ scripts/ tests/        # 42 files already formatted
uv run mypy src/ scripts/                              # Success: no issues found in 19 source files
grep -rn "MagicMock|mocker.patch|unittest.mock" tests/  # no mocks: clean
```

### Left for a future round

- **E1 (open) — `gor_tolerance_multiplier` is still a knob nothing published
  consumes.** The honest caveat stands in `manuscript/02` and `07`. Wiring it in
  would move the reported allowance/session count and re-pin hand arithmetic; it
  was left untouched this round to avoid disturbing published values.
- **E2 (open) — multi-burn rendezvous.** `single_impulse_intercept` still raises
  at the geometric singularities; a two-burn Lambert-style solver would return a
  finite Δv there.
- **E3 (open) — stochastic (PERT) activity durations.** `SHUTTLE_TOTAL_MIN`
  still has no confidence interval; the deterministic CPM total is the stated
  mean case.
- **E5 (open) — `bond-utilities` provenance delegation.** `mission.py` still
  builds its `Provenance` record inline rather than delegating to
  `bond_utilities.mission_io.record_provenance_outcome`.
