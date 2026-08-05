# Agent Instructions — moonraker (mission DRAX)

Read this before modifying anything in the package. It is operational: what to
run, in what order, and what will reject your change.

## Orientation, in order

1. `README.md` — what the package is and every module in one line each.
2. `docs/architecture.md` — the layer contract and how `mission.py` implements
   the frozen `MissionProvider`.
3. `docs/testing_philosophy.md` — why the tests look the way they do.
4. `TODO.md` — what is genuinely still open.

## Hard rules

1. **Scope is exactly this directory.** Never edit a sibling BOND package, the
   bond root files, or the template repo. This is a local-only tree with no
   remote: commit here, never push.
2. **Zero mocks.** No `unittest.mock`, `MagicMock`, `@patch` or
   `create_autospec` in `tests/`. Real parameters through real functions. A mock
   can pass while the arithmetic is wrong.
3. **Thin orchestrators, fat core.** `scripts/` may bootstrap `sys.path`, parse
   argv, call into `src/`, and print. Any arithmetic in a script is a bug —
   it escapes the coverage gate and the single-source rule at once.
4. **Pure domain core.** The seven L0 modules import stdlib only. Only
   `mission.py` imports `bond_api`. Nothing imports `infrastructure.*`.
5. **One computation.** New metrics go through
   `mission_results.compute_mission_results` (or one of its factories). Never
   recompute a published number in a script, a figure, or the manuscript.
6. **Never hand-author a metric in prose.** Numbers reach the manuscript as
   `{TOKEN}` from `manuscript/config.yaml` + `manuscript_variables.py`. If you
   want to state a new quantity, add the variable first, then reference the
   token.
7. **Report what the model computes.** If a result contradicts the film, the
   README, or a previous draft, change the prose — not the model. The centrifuge
   certification is the standing example.
8. **Do not change the protocol surface.** `brief`/`recon`/`plan`/`execute`/
   `debrief`, and the module-level `MissionProvider`, `PROVIDER`, `provider`,
   `GADGETS`, `FILM`, `CODENAME` exports are consumed across the suite. Deepen
   inside; leave the seam alone.
9. **Deterministic.** Fixed seeds, no RNG, no wall-clock in persisted artifacts.

## The loop for a typical change

```bash
uv sync --extra dev                       # once, or after editing pyproject.toml

# 1. write the failing test first, beside its module
uv run pytest tests/test_<module>.py -q

# 2. implement in src/moonraker/, not in scripts/
uv run pytest tests/ --cov=src --cov-fail-under=90 -q

# 3. if you added or changed a metric, regenerate and re-read the artifacts
uv run python scripts/run_mission.py
uv run python scripts/z_generate_manuscript_variables.py
cat output/data/manuscript_variables.json      # confirm the value you expect

# 4. update prose that the change affects: manuscript sections, README, docs/
# 5. gates
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Adding a domain module

- Place it in `src/moonraker/`, stdlib-only, with full type hints and a
  module docstring stating the model and its source.
- Validate inputs and raise `ValueError` with the offending value in the
  message. Where the model genuinely has no answer (a singular geometry, an
  impossible transfer), raise rather than returning a plausible-looking number.
- Export it from `__init__.py` and add its concepts to the `__init__` docstring.
- Add its callables to `_register_gadgets()` in `mission.py` if the orchestrator
  should be able to reach them.
- If it produces a published metric, add a factory in `mission_results.py` and a
  token in `compute_mission_results`.
- Document it in `README.md`, `docs/architecture.md`, and the manuscript
  methodology + results.

## Verification checklist before "done"

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
grep -rn "MagicMock\|mocker.patch\|unittest.mock" tests/ || echo "no mocks: clean"
grep -rn "template[_]code_project" --include='*.py' --include='*.md' . || echo "no lineage strings: clean"
git status --short                        # clean after your commit
```

## Failure modes seen in this package

- **A validated-but-unused argument.** `duration_limit_s` was range-checked and
  then never read, so a ceiling that looked enforced could not reject anything.
  When you add a limit, add the test where it — and only it — causes rejection.
- **Prose contradicting its own token.** The results section rendered
  "`CENTRIFUGE_SAFE` = no" and then, in the same sentence, called the profile
  "comfortably inside the tolerance envelope". Read the *resolved* output under
  `output/manuscript/`, not the template, when checking a claim.
- **Hardcoded constants inside a parameterised branch.** `execute()` took a
  centrifuge radius from the step params but computed RPM against a literal, so
  varying the plan silently did nothing.
- **A silently-skipped step.** An unknown `step.action` used to fall through and
  still increment `steps_completed`, reporting success for a computation that
  never ran.
