# Reproducibility

## Determinism guarantees

Every module in this package is deterministic by construction:

- The three domain cores use only closed-form math (CPM, Kepler's laws, the
  centrifuge physics) with a fixed parameter set — no RNG, no wall-clock.
- `moonraker/mission.py` carries a fixed seed and a stable SHA-256
  `input_hash` over its serialized plan, so any outcome can be audited without
  re-running the film.
- Running `scripts/run_mission.py` regenerates the same results, figures and
  JSON byte-for-byte.

## Verification gate

`uv run pytest tests/ --cov=src --cov-fail-under=90` enforces ≥90% line and
branch coverage with zero mocks (real computation only, per the suite's
zero-mock policy).
