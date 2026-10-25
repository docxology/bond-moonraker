# Moonraker: DRAX — Special-Agent Mission Software

A `PROJECT BOND` suite package (film: **Moonraker**, 1979 · mission codename
**DRAX**). It implements the technical concepts of the DRAX operation as a
deterministic, fully-tested scientific package, and exposes them through the
frozen **BOND-API** `MissionProvider` protocol.

**Published package.** The repository is
<https://github.com/docxology/bond-moonraker>. Its working tree is a sibling of
the `bond-api` checkout it depends on (`[tool.uv.sources]` in `pyproject.toml`
resolves `bond-api` as `../bond-api`), so both must sit side by side to
`uv sync`.

## The film, as a specification

*Moonraker* has three technical spines. Each becomes a concept area here, and
each concept area is carried by pure, independently testable modules.

| Film concept | What it becomes |
|---|---|
| A space shuttle hijacked against a launch deadline | A critical-path activity network, plus the time-cost economics of compressing it when the window closes early |
| Drax's orbital station, resupplied from the ground | Kepler orbit physics, ground launch windows, consumables capacity, a Hohmann resupply transfer with a propellant budget, and a Clohessy–Wiltshire final approach |
| The centrifuge chamber Bond is put through at Drax's facility | A ramp/sustain/decay g-profile adjudicated against a +Gz tolerance envelope, and a weekly regimen bounded by exposure caps |

The package is concept-faithful, not cosmetic: the models are real physics and
real scheduling mathematics, and they are allowed to disagree with the film. The
centrifuge certification does exactly that — see *Results*, below.

## Modules

Every module in `src/moonraker/`, one line each.

| Module | What it computes |
|---|---|
| `shuttle_ops.py` | Critical Path Method over the hijack activity network — forward/backward pass, slack, the zero-slack activity set *and* the enumerated critical paths (the DRAX network has two), cycle and dangling-dependency rejection, and feasibility against the point of no return |
| `schedule_crashing.py` | Minimum-cost time-cost crashing over a network *derived* from the canonical timeline: re-solve the CPM, buy down the cheapest zero-slack activity a minute at a time, report cost, minutes bought, and whether the deadline is reachable at all |
| `orbital_logistics.py` | Kepler period and circular speed, orbits per sidereal day, horizon/pass geometry, the deterministic ground launch-window series and the horizon filter that bounds how many of them are usable, and the consumables ↔ crew ↔ cadence model |
| `orbital_transfer.py` | Vis-viva, the Hohmann two-burn transfer and its time, the phase wait to the lead angle, the Tsiolkovsky mass ratio and propellant mass, and the deorbit burn |
| `rendezvous.py` | Clohessy–Wiltshire relative motion in the LVLH frame: the 6×6 state transition, propagation, and the closed-form single-impulse intercept (raising at singular geometries) |
| `centrifuge.py` | g↔rpm centripetal physics, the +Gz tolerance envelope, the ramp/sustain/decay profile builder, and the two-ceiling safety adjudication |
| `centrifuge_training.py` | g·s exposure dosing and weekly session planning under daily and cumulative caps. Gradual-onset-rate tolerance scaling is implemented and tested but **not** consumed by any published result — the reported regimen is onset-rate–independent |
| `mission_results.py` | The single canonical computation — mission parameters in, the flat token-keyed result set out, assembled entirely from its seven `compute_*` factories. The mission adapter, the token map and the figures all read these |
| `mission.py` | The BOND-API `MissionProvider` adapter and the module-level `GADGETS` registry |
| `manuscript_variables.py` | Token-map hydration from `config.yaml` + results, and resolution of the manuscript tree into `output/manuscript/` |
| `figures.py` | Five deterministic matplotlib figures under the headless `Agg` backend, every value read from `mission_results` — the module declares no mission constant of its own |

The first seven are the pure domain core: stdlib only, no `bond_api`, no
`infrastructure`, no RNG, no wall-clock. They import and compute in isolation.

## Layout

```
src/moonraker/     seven pure domain modules + composition, adapter, presentation
scripts/           one thin CLI per mission phase, plus the flagship runner
tests/             per-module + protocol + smoke tests (zero mocks)
manuscript/        config.yaml, references.bib, tokenised DRAX sections
docs/              architecture, agent instructions, testing philosophy
output/            regenerable artifacts (git-ignored, never hand-edited)
```

`mission.py` is the only module coupled to `bond-api`; see
`docs/architecture.md` for the full layer contract.

## Quick start

```bash
uv sync --extra dev                                       # deps + bond-api path dependency

uv run python scripts/run_mission.py                      # full flow + all artifacts
uv run python scripts/brief.py                            # ... or one phase at a time
uv run python scripts/z_generate_manuscript_variables.py  # hydrate + resolve tokens

uv run pytest tests/ --cov=src --cov-fail-under=90        # the gate (>=90% line+branch)
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

Measured test count and coverage live in `docs/_generated/COUNTS.md`, regenerated
from the gate. This README deliberately does not restate them — a figure typed
into prose is stale from the next commit onward.

## Results

Every published number is computed, never typed. After
`scripts/run_mission.py`, read them at:

- `output/data/mission_results.json` — the canonical result set
- `output/data/manuscript_variables.json` — the same values as manuscript tokens
- `output/manuscript/03_results.md` — the results section with tokens resolved
- `output/figures/*.png` — five figures

Qualitatively, the mission finds: the hijack timeline is feasible inside its
point of no return and can be crashed to a tighter deadline at a computable
minimum cost; the station's stores and cadence bound a specific sustainable
crew, reachable by a Hohmann transfer whose Δv and propellant the model sizes;
and — the one negative verdict — **the canonical 6 g centrifuge profile is not
certified**, because its plateau overruns the tolerance allowance at that peak.
The manuscript reports the exceedance and the plateau length that would pass.
That result is pinned by `tests/test_mission_results.py` in both directions, so
it cannot silently flip or be quietly written around.

## Mission provider

`src/moonraker/mission.py` exposes, at module top level, the frozen surface the
rest of the suite consumes: `MissionProvider` (slug `moonraker`, codename
`DRAX`), the `PROVIDER` singleton, the `provider()` factory, the `GADGETS`
registry, and `FILM` / `CODENAME`.

It implements all five lifecycle stages — `brief` → `recon` → `plan` →
`execute` → `debrief` — deterministically: no state, a fixed seed,
`wall_time_s = 0.0`, and a stable SHA-256 `input_hash` over the serialized plan.
Its domain callables are registered as gadgets with the BOND-API
`GadgetRegistry`, and the package is discoverable by slug through
`bond_api.discovery.load_provider("moonraker")`.

This surface is **frozen**: `bond-cli`, the coordinator and the orchestrator
consume it across packages. Deepen inside the package; do not rename or reshape
the seam.

## License

MIT.
