# tests/ — Test Suite (moonraker / DRAX)

## Overview

Tests validate the DRAX mission package: critical-path hijack timeline, Drax
station orbital logistics, centrifuge g-profiles, the BOND-API mission
provider, and the script CLIs — all with real computation and zero mocks.

## Key concepts

- **Real data testing**: no mocks; every assertion runs actual math.
- **Deterministic results**: fixed inputs, fixed seed, no wall-clock.
- **Protocol conformance**: `test_mission.py` asserts the provider satisfies
  the runtime-checkable `MissionProvider` protocol and is discoverable by slug.
- **Live cross-reference**: `test_manuscript_variables.py` enforces every
  `{{TOKEN}}` in numbered prose sections exists in `generate_variables()`.

## Run

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```
