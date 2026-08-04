# Convention — scripts/ (moonraker / DRAX)

- **Thin only.** No design math in scripts; delegate to `moonraker.*`.
- **Deterministic runs.** `run_mission.py` regenerates byte-identical outputs.
- **argv shaping.** Tiny argv defaults are acceptable (e.g. `recon.py` defaults
  the goal); keep the logic trivially readable.
- **Exit codes.** 0 on success; script smoke tests assert `returncode == 0`.
