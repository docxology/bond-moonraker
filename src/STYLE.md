# Source Code Style Guide — moonraker (DRAX)

Code style and design conventions for the moonraker package.

## Pure Function Design

Functions in the domain core (`shuttle_ops`, `orbital_logistics`,
`centrifuge`, `mission_results`) are **side-effect-free**: they take inputs and
return outputs, with no I/O and no global mutation. This keeps them
infrastructure-free and deterministically testable.

## Determinism

- Fixed parameter sets; no untracked RNG.
- No wall-clock time in persisted artifacts (`Provenance.wall_time_s == 0.0`).
- The canonical result computation (`compute_mission_results`) is the single
  source every consumer shares.

## Layer discipline

- Only `mission.py` imports `bond_api`.
- `scripts/` are thin CLIs (bootstrap + delegate); no math in scripts.

## Conventions

- Full type hints on public functions; docstrings with Args/Returns.
- Validation raises `ValueError` with an actionable message on invalid input.
- Match ruff defaults (88-col) and pass `ruff check` + `ruff format`.
