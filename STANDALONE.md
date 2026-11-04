# Standalone package identity — moonraker (DRAX)

This is a **standalone** `PROJECT BOND` package: it carries no DOI or
publication record, and its only suite dependency is the `bond-api` protocol
package, recorded in `vendor/bond-api` (upstream sha and per-file digests in
its `PROVENANCE.json`, verified offline by `scripts/vendor.py --check`), so the
clone resolves without a sibling checkout. The repository is published at
<https://github.com/docxology/bond-moonraker>.

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

## Repo contract

- Commits stay inside this repository and are path-scoped.
- `output/` is regenerable and git-ignored.
