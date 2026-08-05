# Live test count and coverage — moonraker (mission DRAX)

Recomputed by the package gate; do not hand-edit without re-running:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

| Metric | Value | Measured |
|---|---|---|
| Passing tests | 178 | 2026-08-05 |
| Line + branch coverage on `src/` | 99.91% | 2026-08-05 |
| Failed / skipped | 0 / 0 | 2026-08-05 |
| Mocks used | 0 | 2026-08-05 |

Per-module coverage at that measurement: every module in `src/moonraker/` at
100.00% except `manuscript_variables.py` at 98.36% (one uncovered branch on the
strict-mode guard).

Figures generated: `timeline_critical_path.png`, `orbit_period_windows.png`,
`centrifuge_g_profile.png`, `hohmann_transfer.png`,
`training_weekly_load.png` (via `scripts/run_mission.py`).
