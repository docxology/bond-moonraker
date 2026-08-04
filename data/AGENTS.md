# Data directory — agent guide (moonraker / DRAX)

Versioned project **inputs** only; pipeline outputs must not be committed
here.

## `claim_ledger.yaml`

Evidence registry for manuscript claims sourced from code / generated
artifacts rather than `{{TOKEN}}` injection. Schema: `claim_id`, `kind`,
`value`, `source`, `source_tier`, `freshness`, `artifact_path`.

## Rules

- Update only when source-backed numeric facts change.
- Keep values consistent with `src/moonraker/mission_results.py` and
  `output/data/mission_results.json`.
- Never store generated JSON/CSV/PNG under `data/`.
