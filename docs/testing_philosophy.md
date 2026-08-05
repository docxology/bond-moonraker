# Testing Philosophy — moonraker (mission DRAX)

## The gate

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

≥90% **line and branch** coverage on `src/`, zero failures, zero skips. Live
counts are in `docs/_generated/COUNTS.md` — read them there rather than trusting
a number written into prose, because prose does not recompute itself.

## Zero mocks, and why it is not a style preference

No `unittest.mock`, no `MagicMock`, no `mocker.patch`, no `create_autospec`
anywhere in `tests/`. Where a collaborator is genuinely needed, a deterministic
fake implements the **real** protocol.

This package is the argument for the rule. Everything here is arithmetic:
Kepler periods, vis-viva speeds, a Clohessy–Wiltshire state transition, a
power-law tolerance envelope. A mocked `orbital_period` returning 5483.6 proves
that the caller reads a float. It proves nothing about whether the exponent on
the semi-major axis is 3 or 2. Only running the real function against a
hand-checkable case does that. A green suite built on mocks would have told us
the centrifuge module was fine — the real computation is what revealed that the
canonical DRAX profile fails certification.

## What the suite actually covers

| File | Binds |
|---|---|
| `test_shuttle_ops.py` | CPM on the canonical network, plus degenerate cases: linear chain, parallel branch with slack, cycle → `ValueError`, non-tuple input normalisation |
| `test_schedule_crashing.py` | Greedy crash correctness, cost accounting, the infeasible case where full compression still misses the deadline, and validation branches |
| `test_orbital_logistics.py` | Kepler/vis-viva internal consistency, visibility geometry, launch-window spacing, the consumables closed forms, and every validation branch |
| `test_orbital_transfer.py` | Hohmann burns, phase-wait sign conventions, rocket-equation round trips, deorbit geometry, refusal of coincident/sub-surface orbits |
| `test_rendezvous.py` | STM structure, propagation consistency, the intercept closed form, and the singular geometries that must raise |
| `test_centrifuge.py` | g↔rpm round trips, envelope shape, profile discretisation, **both** duration ceilings, and the pinned DRAX certification verdict |
| `test_centrifuge_training.py` | GOR monotonicity and clamping, g·s dosing, cap arithmetic, and the validation edges (bad ceiling type, non-advancing time samples) |
| `test_mission.py` | Protocol conformance by `isinstance`, all five stages, determinism of results and `input_hash`, gadget registration, discovery by slug, unknown-action refusal, and that step params actually reach the computation |
| `test_mission_results.py` | The canonical metric set, determinism, parameter overrides, the pinned centrifuge verdict in both directions, and that every config knob moves a result |
| `test_manuscript_variables.py` | Token map construction, strict vs draft mode, and the live cross-reference over every numbered section on disk |
| `test_figures.py` | Each figure renders a valid PNG |
| `test_scripts_smoke.py` | Every phase CLI and the flagship runner exit 0 and write the expected artifacts |

## Three rules that keep tests meaningful

**1 · A test must be able to fail.** A parameter that is validated but never
read produces a check that cannot reject anything. `profile_is_safe` carried
exactly that defect: `duration_limit_s` was range-checked and then ignored. The
fix was to make it govern, and the test that proves it does is deliberately
discriminating — the same profile passes at one limit and is refused at another,
so the assertion would fail if the argument went dead again.

**2 · Pin the verdicts prose depends on.** The manuscript reports the centrifuge
certification through a token. `TestComputeMissionResults` pins that verdict
*and* pins the flip under a shortened plateau. Either direction of silent drift
breaks a test before it can quietly contradict the paper.

**3 · Bind config knobs to outcomes.** `TestConfigKnobsAreConsumed` flips each
mission parameter and asserts the result moves. A knob that is named in
`config.yaml`, documented in the setup table, and read by nothing advertises
control the model does not have.

## Determinism

Fixed parameter sets, a fixed seed, no RNG anywhere in `src/`, and no wall-clock
value in any persisted artifact (`Provenance.wall_time_s` is `0.0` on purpose —
a timing figure would make otherwise-identical runs differ). `run_mission.py`
restores a byte-identical `output/` tree on re-run, which is the determinism
proof rather than a claim about it. Matplotlib runs under `Agg`, forced in
`tests/conftest.py`, so figure tests do not depend on a display.

## Adding a test

Put it beside its module (`tests/test_<module>.py`), assert against a value you
can derive by hand or from an independent identity (a round trip, a conservation
law, a monotonicity), and prefer a case that would fail under a plausible bug
over one that merely exercises a line. Coverage is a floor, not the goal: a test
that runs a function and asserts `is not None` moves the percentage and binds
nothing.
