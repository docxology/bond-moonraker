# tests/ — moonraker test suite

Zero-mock, deterministic tests for the DRAX mission package.

## Run

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

Live test count + coverage: `docs/_generated/COUNTS.md`. Read the measured
numbers there — never restate them here, where nothing recomputes them.

## Coverage map

- `test_shuttle_ops.py` — CPM correctness + degenerate/error networks.
- `test_schedule_crashing.py` — greedy crash, cost accounting, infeasible case.
- `test_orbital_logistics.py` — Kepler, visibility, windows, consumables.
- `test_orbital_transfer.py` — vis-viva, Hohmann, phase wait, propellant, deorbit.
- `test_rendezvous.py` — CW state transition, propagation, singular geometries.
- `test_centrifuge.py` — g↔rpm, tolerance, profile shape, both safety ceilings.
- `test_centrifuge_training.py` — GOR scaling, g·s dosing, cap arithmetic.
- `test_mission.py` — protocol conformance, full flow, determinism, gadgets,
  discovery.
- `test_mission_results.py` — canonical metric set + overrides.
- `test_manuscript_variables.py` — token map + live `{{TOKEN}}` cross-ref.
- `test_figures.py` — figure PNG rendering.
- `test_scripts_smoke.py` — phase CLIs + flagship runner (exit 0, artifacts).

## What a good test looks like here

Assert against a value derivable by hand or from an independent identity (a
round trip, a conservation law, a monotonicity). Prefer a case that fails under
a plausible bug over one that merely executes a line — coverage is a floor, not
the goal. Where prose depends on a verdict, pin the verdict in both directions.
See `../docs/testing_philosophy.md`.
