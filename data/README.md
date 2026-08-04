# moonraker/data

Project-maintained **inputs** for the moonraker (DRAX) package — not pipeline
outputs.

## Contents

- `claim_ledger.yaml` — evidence registry for source-backed manuscript claims
  (all values computed from `src/moonraker/`, never hand-authored).

## Edit protocol

1. Update only when source-backed numeric facts change.
2. Keep the values consistent with `src/moonraker/mission_results.py` and
   `output/data/mission_results.json`.
3. Do not store generated JSON/CSV/PNG under `data/`.
