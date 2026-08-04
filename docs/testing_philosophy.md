# Testing Philosophy — moonraker (mission DRAX)

## Zero-mock policy

All tests exercise real algorithms with real parameters. Deterministic fakes
subclass/implement the REAL protocol where a collaborator is needed; there are
no mocked objects or faked side effects. The gate command:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Live test count and coverage are tracked in `docs/_generated/COUNTS.md`
(currently 98 tests, 99.14% line+branch on `src/`).

## What the suite covers

- `test_shuttle_ops.py` — CPM correctness on the canonical network plus
  degenerate networks (linear, parallel-with-slack, cycle → error).
- `test_orbital_logistics.py` — Kepler consistency, visibility geometry, launch
  window spacing, consumables closed forms, and every validation branch.
- `test_centrifuge.py` — g↔rpm round-trips, tolerance envelope, profile shape,
  safety checks, and validation branches.
- `test_mission.py` — protocol conformance (`isinstance` against the
  runtime-checkable `MissionProvider`), full `run_mission` flow, determinism,
  gadget registration, and discovery by slug via `bond_api.discovery`.
- `test_mission_results.py` — the canonical metric set, determinism, overrides.
- `test_manuscript_variables.py` — token map + the live `{{TOKEN}}`
  cross-reference over every numbered prose section.
- `test_figures.py` — each figure renders a valid PNG.
- `test_scripts_smoke.py` — the phase CLIs and the flagship runner return
  exit 0 and write the expected artifacts.

## Determinism

Fixed parameter sets, fixed seed, no wall-clock in persisted artifacts;
`run_mission.py` restores a byte-identical `output/` on re-run.
