# Standalone / local package identity — moonraker (DRAX)

This is a **local-only** `PROJECT BOND` package: it lives at
`projects/working/bond/moonraker/`, is never pushed to any remote, and carries
no DOI or publication record.

## Identity

- Package: `moonraker` (film *Moonraker*, 1979)
- Mission codename: `DRAX`
- Version: `0.2.0`
- License: MIT
- Suite: PROJECT BOND (bond-api, bond-orchestrator, bond-utilities, + film
  packages)

## Protocol

- Implements the frozen BOND-API `MissionProvider` protocol in
  `src/moonraker/mission.py` (slug `moonraker`, codename `DRAX`).
- Registered with the BOND suite via `bond_api` discovery + `GadgetRegistry`;
  the orchestrator consumes it by slug.

## Local-only contract

- No remote, never push. `git add -A` only inside this repo, path-scoped
  commits.
- `output/` is regenerable and git-ignored.
