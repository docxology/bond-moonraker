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
| `run_mission.py` | Flagship: full flow + write `output/data/mission_results.json`, render all five figures |
| `z_generate_manuscript_variables.py` | Hydrate `{{TOKEN}}`s into `output/data/` + `output/manuscript/` |

## Protocol

- Scripts import from `moonraker.*`, never from `src/` internals directly.
- `z_generate_manuscript_variables.py` is strict by default (requires
  `output/data/mission_results.json`); `--allow-draft` relaxes it.
- Run `uv run python scripts/<name>.py` from the package root.

## The thin-orchestrator rule, concretely

A script may bootstrap `sys.path`, parse argv, call into `src/`, write a file,
and print. It may not compute a published number. Arithmetic in a script escapes
the `--cov=src` gate and forks the single-source rule at the same time: the value
it produces can then disagree with the identically-named manuscript token. If a
script needs a number, add it to `mission_results.compute_mission_results` and
read it from there.
