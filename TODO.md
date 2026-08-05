# TODO — moonraker (mission DRAX)

Remaining work only. What is already built is described in `README.md` (module
table), `docs/architecture.md` (per-module detail) and the manuscript — this file
does not duplicate them.

## Open

### Domain

- [ ] **Multi-burn rendezvous.** `single_impulse_intercept` raises at the
  geometric singularities (whole-period intercept times, in-plane degeneracies)
  because no single impulse exists there. A two-burn Lambert-style solver would
  return an answer instead of an exception. Acceptance: the singular cases in
  `tests/test_rendezvous.py` gain a companion assertion that the multi-burn path
  returns a finite, verified Δv.
- [ ] **Stochastic activity durations.** The hijack network is deterministic
  CPM, so `SHUTTLE_TOTAL_MIN` has no confidence interval. A PERT three-point
  estimate per activity would give one. Acceptance: a new token reporting the
  interval, with the deterministic total unchanged as the mean case.
- [ ] **Orbit decay.** `orbital_logistics` uses ideal circular two-body orbits,
  so the launch-window series never precesses and the station never loses
  altitude. A drag/J2 term would make the resupply cadence a function of time.
  Acceptance: documented as an extension, or the scope note in
  `manuscript/07_scope_and_related_work.md` stays as the honest boundary.
- [ ] **`gor_tolerance_multiplier` is computed but unpublished.** It is tested
  and exported, and the methodology describes it, but no mission result or
  manuscript token consumes it. Either wire it into `compute_training` (so a
  slower onset rate widens the allowance) or drop it. Leaving it half-connected
  is the shape of a knob that does nothing.

### Manuscript

- [ ] **Centrifuge remediation as a computed recommendation.** §Results states
  the plateau that *would* pass by pointing at `CENTRIFUGE_ALLOWABLE_S`. A
  dedicated `compute_*` factory returning a certified-by-construction profile
  (shortened plateau, or reduced peak) would make the recommendation a first
  class result rather than a reader's inference.

### Integration

- [ ] **`bond-utilities` provenance.** If the suite standardises on
  `bond_utilities.mission_io.record_provenance_outcome`, `mission.py execute()`
  should delegate its `Provenance` record through it. Acceptance: no signature
  change to `MissionOutcome`, `wall_time_s` still `0.0`, `input_hash` unchanged
  for an unchanged plan.

## Done and verified (do not re-open)

- **bond-api integration** — local path dependency; `mission.py` adapts the
  frozen protocol; discovery by slug works via `bond_api.discovery`.
- **bond-coordinator / bond-orchestrator** — consume the provider by slug; no
  moonraker-side change is required.
- **Phase-4 deepening** — `orbital_transfer`, `rendezvous`,
  `centrifuge_training` and `schedule_crashing` are built, tested, registered as
  gadgets, and written into the manuscript.
- **Phase-5 defect pass** — the following were found and fixed, each with a test
  that would catch a regression:
  - `centrifuge.profile_is_safe` validated `duration_limit_s` and then never
    used it: a ceiling that could not reject anything.
  - `manuscript/03_results.md` rendered the "not certified" verdict token and
    then called the profile "comfortably inside the tolerance envelope" in the
    same sentence; `README.md` asserted it was safe outright.
  - `mission.execute` computed centrifuge RPM against a hardcoded arm radius
    while taking the profile from the step params, and hardcoded the consumables
    parameters, so varying a plan silently did nothing.
  - `mission.execute` incremented `steps_completed` for an unknown
    `step.action`, reporting success for a computation that never ran.
  - `centrifuge_training.gor_tolerance_multiplier` had an unreachable ceiling
    check after the floor check, so a non-numeric ceiling escaped as a
    `TypeError`.
  - `manuscript_variables._environment_probe` was dead code; `shuttle_ops`
    carried an unused `remaining` list in its cycle detector.
  - `references.bib` credited *Moonraker* to "Wood, John" — the film was
    directed by Lewis Gilbert from a screenplay by Christopher Wood.

## Notes

- `output/` is git-ignored and regenerable; `scripts/run_mission.py` restores a
  byte-identical tree on re-run.
- Measured coverage and test counts: `docs/_generated/COUNTS.md`. Do not quote
  them elsewhere in prose.
