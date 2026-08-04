# Live test count and coverage — moonraker (mission DRAX)

Recomputed by the package gate; do not hand-edit without re-running:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

| Metric | Value |
|---|---|
| Passing tests | 164 |
| Line + branch coverage on `src/` | 99.20% |
| Failed / skipped | 0 / 0 |
| Mocks used | 0 |

Figures generated: `timeline_critical_path.png`, `orbit_period_windows.png`,
`centrifuge_g_profile.png`, `hohmann_transfer.png`,
`training_weekly_load.png` (via `scripts/run_mission.py`).
