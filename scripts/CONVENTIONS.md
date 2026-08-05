# Convention — scripts/ (moonraker / DRAX)

- **Thin only.** No design math in scripts; delegate to `moonraker.*`.
- **Deterministic runs.** `run_mission.py` + `z_generate_manuscript_variables.py`
  regenerate byte-identical outputs on the same interpreter and platform. No
  script or module on that path may read the wall clock — bound by
  `tests/test_regeneration_determinism.py`.
- **argv shaping.** Tiny argv defaults are acceptable (e.g. `recon.py` defaults
  the goal); keep the logic trivially readable.
- **Exit codes.** 0 on success; script smoke tests assert `returncode == 0`.
