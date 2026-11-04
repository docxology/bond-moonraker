# Live test count and coverage — moonraker (mission DRAX)

Recomputed by the package gate; do not hand-edit without re-running:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

| Metric | Value | Measured |
|---|---|---|
| Passing tests | 257 | 2026-11-04 |
| Line + branch coverage on `src/` | 100.00% | 2026-11-04 |
| Failed / skipped | 0 / 0 | 2026-11-04 |
| Mocks used | 0 | 2026-11-04 |

Re-measured 2026-11-04 with Python 3.15.1 and ruff 0.17.2 (the lock's pin):
`ruff check` clean on `src/`, `scripts/`, `tests/` (44 files formatted), `mypy
src/ scripts/` clean in 20 source files, and `run_mission.py` +
`z_generate_manuscript_variables.py` regenerate `output/` byte-identically
(digest `c43db2b2a7356b9e` twice).

Per-module coverage at that measurement: every module in `src/moonraker/` at
100.00% line + branch (the last remaining gap, the strict-mode guard in
`manuscript_variables.py`, was closed in round 2 by a positive-control unit
test).

Figures generated: `timeline_critical_path.png`, `orbit_period_windows.png`,
`centrifuge_g_profile.png`, `hohmann_transfer.png`,
`training_weekly_load.png` (via `scripts/run_mission.py`).
