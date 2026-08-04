# scripts/ — moonraker thin orchestrators

One thin CLI per mission phase plus a flagship runner and the manuscript
variable generator. All business logic lives in `src/moonraker/`; these scripts
only bootstrap `sys.path`, parse argv, and delegate.

| Script | Purpose |
|---|---|
| `brief.py` | Print the DRAX mission brief |
| `recon.py` | Run reconnaissance for a goal |
| `plan.py` | Print the mission execution plan |
| `execute.py` | Execute the plan + print computed results |
| `debrief.py` | Run the full flow + print lessons |
| `run_mission.py` | Flagship: full flow + write `output/data/mission_results.json`, render figures |
| `z_generate_manuscript_variables.py` | Hydrate `{{TOKEN}}`s into `output/data/` + `output/manuscript/` |

## Protocol

- Scripts import from `moonraker.*`, never from `src/` internals directly.
- `z_generate_manuscript_variables.py` is strict by default (requires
  `output/data/mission_results.json`); `--allow-draft` relaxes it.
- Run `uv run python scripts/<name>.py` from the package root.
