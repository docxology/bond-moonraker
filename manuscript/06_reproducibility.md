# Reproducibility

## Determinism guarantees

Every module in this package is deterministic by construction:

- The seven domain modules use only closed-form mathematics — CPM and greedy
  time-cost crashing, Kepler's laws, the vis-viva and Tsiolkovsky relations, the
  Clohessy–Wiltshire state transition, and the centrifuge physics — over a fixed
  parameter set. There is no RNG anywhere in `src/`, no wall-clock input to any
  computation, and no network or filesystem read inside the domain core.
- `moonraker/mission.py` carries a fixed seed and records a stable SHA-256
  `input_hash` over the serialized plan plus package identity, so an outcome can
  be audited without re-running the mission. `Provenance.wall_time_s` is
  deliberately `0.0`: a timing figure would make otherwise-identical runs differ.
- `moonraker/mission_results.py` is the single canonical computation. Its
  factories (`compute_schedule`, `compute_orbit`, `compute_centrifuge`,
  `compute_transfer`, `compute_rendezvous`, `compute_training`,
  `compute_crash`) are what the mission `execute()` adapter, the manuscript
  token map **and** `moonraker/figures.py` all call, each on the same parameter
  dict read from `manuscript/config.yaml`. No figure declares a mission
  constant of its own — `tests/test_figures.py` parses the module and fails if
  one reappears — so an outcome value, its injected token and the plotted
  figure cannot disagree.
- Figures are rendered through the headless `Agg` backend with fixed inputs.
- `moonraker/manuscript_variables.py` reads no wall clock. The manuscript's
  date token, `MANUSCRIPT_DATE`, is the committed `paper.date` field of
  `manuscript/config.yaml`, not the moment the generator ran, and
  `generate_variables()` takes no `now` argument that could reintroduce one.

Running `scripts/run_mission.py` followed by
`scripts/z_generate_manuscript_variables.py` restores a byte-identical
`output/` tree — every file, on any later re-run, on the same interpreter and
platform. The scope of that claim is exact: two token values, `PYTHON_VERSION`
and `PLATFORM`, are read from the running interpreter, so they change if the
package is regenerated on a different machine or Python build. Nothing else in
the tree varies. Elapsed time in particular does not: `Provenance.wall_time_s`
is pinned to `0.0` and no date or timestamp is sampled anywhere.

`TestRegenerationIsByteIdentical` in `tests/test_regeneration_determinism.py`
binds this end to end — it runs both scripts twice into an isolated tree and
compares a SHA-256 of every regenerated file — and
`TestNoWallClockInPersistedPath` parses every module under `src/moonraker/` and
`scripts/` and fails on any wall-clock call, with a positive control proving
the parser detects one when it is present. An earlier version of this section
claimed byte-identity while the abstract carried a `datetime.now()` timestamp;
the only test guarding it injected a fixed `now`, which is precisely why the
contradiction survived.

## What a reader can re-derive

| Artifact | Command |
|---|---|
| `output/data/mission_results.json` | `uv run python scripts/run_mission.py` |
| `output/figures/*.png` (five figures) | `uv run python scripts/run_mission.py` |
| `output/data/manuscript_variables.json` | `uv run python scripts/z_generate_manuscript_variables.py` |
| `output/manuscript/` (token-resolved prose) | `uv run python scripts/z_generate_manuscript_variables.py` |

`output/` is git-ignored throughout: it is regenerable, never authoritative, and
never hand-edited.

## Verification gate

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

The coverage gate enforces ≥90% line **and** branch coverage on `src/` with zero
mocks — no `unittest.mock`, no `MagicMock`, no monkeypatched collaborators in the
domain tests. Every assertion runs the real algorithm on real parameters.

Two test classes exist specifically to keep this manuscript honest.
`TestLiveCrossReference` in `tests/test_manuscript_variables.py` reads every
numbered section on disk and fails if any brace-delimited token it uses is
absent from the generated map, so prose can never reference a variable that no longer exists.
`TestComputeMissionResults` pins the centrifuge certification verdict in both
directions, so the negative result reported in §Results cannot silently invert.
`TestConfigKnobsAreConsumed` sweeps **every** key in `MISSION_DEFAULTS` — the
probe table must cover the parameter set exactly, so a knob added without one
fails the suite — and asserts each one moves at least one published value when
flipped. One knob, the peak-g ceiling, is exercised from a shortened plateau
rather than the shipped defaults, because the DRAX plateau already fails the
duration ceiling and no peak-g value could change that verdict; the test says
so in place.
