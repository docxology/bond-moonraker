# scripts/ — Thin Orchestrators (moonraker / DRAX)

Rules for the moonraker scripts.

## Thin-orchestrator pattern

Scripts compose functions from `src/moonraker/`. They never implement math or
perform data mutation themselves — they bootstrap `sys.path`, parse argv, and
delegate.

## Key scripts

- `run_mission.py` — the flagship: runs the five-stage BOND-API mission,
  recomputes `moonraker.mission_results.compute_mission_results()`, writes
  `output/data/mission_results.json`, and renders the three figures into
  `output/figures/`.
- `z_generate_manuscript_variables.py` — strict by default; requires
  `output/data/mission_results.json`. `--allow-draft` relaxes it for early
  drafts.

## Conventions

- Scripts self-insert `src/` into `sys.path` (paired `# noqa: E402` on the
  import lines — the root per-file-ignore patterns do not cover this deep path).
- `output/` is git-ignored and fully regenerable.
