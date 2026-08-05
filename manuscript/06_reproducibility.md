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
- `moonraker/mission_results.py` is the single canonical computation. The
  mission `execute()` adapter, the manuscript token map and the figures all read
  it, so an outcome value and its injected token cannot disagree.
- Figures are rendered through the headless `Agg` backend with fixed inputs.

Running `scripts/run_mission.py` restores a byte-identical `output/` tree. The
only non-reproducible value in the manuscript is the generation timestamp,
which is confined to the abstract and is injectable for tests.

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
