# Live test count and coverage — moonraker (mission DRAX)

Recomputed by the package gate; do not hand-edit without re-running:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

| Metric | Value |
|---|---|
| Passing tests | 98 |
| Line + branch coverage on `src/` | 99.14% |
| Failed / skipped | 0 / 0 |
| Mocks used | 0 |

Figures generated: `timeline_critical_path.png`, `orbit_period_windows.png`,
`centrifuge_g_profile.png` (via `scripts/run_mission.py`).
