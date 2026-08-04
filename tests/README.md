# tests/ — moonraker test suite

Zero-mock, deterministic tests for the DRAX mission package.

## Run

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

Live test count + coverage: `docs/_generated/COUNTS.md` (98 tests, 99.14%).

## Coverage map

- `test_shuttle_ops.py` — CPM correctness + degenerate/error networks.
- `test_orbital_logistics.py` — Kepler, visibility, windows, consumables.
- `test_centrifuge.py` — g↔rpm, tolerance, profile shape, safety.
- `test_mission.py` — protocol conformance, full flow, determinism, gadgets,
  discovery.
- `test_mission_results.py` — canonical metric set + overrides.
- `test_manuscript_variables.py` — token map + live `{{TOKEN}}` cross-ref.
- `test_figures.py` — figure PNG rendering.
- `test_scripts_smoke.py` — phase CLIs + flagship runner (exit 0, artifacts).
