# Moonraker: DRAX — Special-Agent Mission Software

A `PROJECT BOND` suite package (film: **Moonraker**, 1979 · mission codename
**DRAX**). It models three concepts from the DRAX mission as a deterministic,
fully-tested scientific package, and implements the frozen **BOND-API**
`MissionProvider` protocol.

**Local-only working tree.** This package lives in
`projects/working/bond/moonraker/` and never pushes to a remote.

## Concepts

| Module | Concept | Model |
|---|---|---|
| `src/moonraker/shuttle_ops.py` | Space-shuttle hijack timeline | Critical Path Method (CPM) over 8 hijack phases, with feasibility against the shuttle's point of no return |
| `src/moonraker/orbital_logistics.py` | Drax space-station orbital logistics | Kepler orbit physics (period, speed, orbits/day), ground launch windows, consumables capacity & sustainable crew |
| `src/moonraker/centrifuge.py` | Centrifuge g-force training profiles | ramp/sustain/decay g-profile with a physiological g-tolerance envelope and safety check |

All three are pure and infrastructure-free (stdlib + `math` only) and fully
deterministic — no RNG, no wall-clock inputs.

## Architecture

```
src/moonraker/
  shuttle_ops.py           pure CPM hijack timeline
  orbital_logistics.py     pure Kepler / logistics
  centrifuge.py            pure g-profile models
  mission.py               BOND-API MissionProvider adapter + gadget registry
  mission_results.py       canonical deterministic result computation
  manuscript_variables.py  {{TOKEN}} hydration from config + results
  figures.py               deterministic matplotlib figure generators
scripts/                   one thin CLI per mission phase + runner
tests/                     per-module + protocol + smoke tests (zero mocks)
manuscript/                config.yaml + tokenised DRAX sections
```

`mission.py` is the thin adapter to the frozen protocol in `bond-api`; the
domain modules never import it (so they stay importable in isolation).

## Quick start

```bash
uv sync --extra dev            # install deps + bond-api path dependency
uv run python scripts/run_mission.py          # full flow + artifacts
uv run python scripts/brief.py                # ... per-phase CLIs
uv run python scripts/z_generate_manuscript_variables.py  # hydrate tokens

uv run pytest tests/ --cov=src --cov-fail-under=90   # gate (>=90%)
uv run ruff check src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Results (injectable, not hand-authored)

- Hijack timeline completes in **57.0 min** against a 60-min deadline
  (margin 3.0 min).
- Drax station (350 km) has a ~5484 s period; its stores sustain **450 crew**
  on a 6-day resupply cadence.
- A **6.0 g** centrifuge profile (~26 rpm on an 8 m arm) is safe against the
  tolerance envelope.

## Mission provider

`src/moonraker/mission.py` exposes `MissionProvider` at module top level
(slug `moonraker`, codename `DRAX`), implements the five lifecycle stages
(`brief`/`recon`/`plan`/`execute`/`debrief`), and registers its domain
functions as gadgets with the BOND-API `GadgetRegistry`.

## License

MIT.
