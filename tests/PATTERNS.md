# Test patterns — moonraker (DRAX)

## Zero-mock policy

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Where a collaborator is needed (e.g. the BOND-API protocol), the test
uses the REAL protocol types from `bond_api` — never a fake.

## Deterministic invariants

- Fixed parameter sets and a fixed seed.
- Assertions on closed-form values (e.g. `orbital_period(400)`
  `== 2π√(a³/μ)`), never on wall-clock timing.
- Recompute-and-compare for determinism (e.g.
  `compute_mission_results() == compute_mission_results()`).

## Validation-branch coverage

Each module's `ValueError` branches are tested directly (empty networks,
non-positive durations, cyclic dependencies, bad elevation/radius inputs,
bad safety margins) so the ≥90% line+branch gate holds across all paths.
