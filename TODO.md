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
  and exported, but no mission result, manuscript token or figure consumes it.
  Either wire it into `compute_training` (so a slower onset rate widens the
  allowance) or drop it. Leaving it half-connected is the shape of a knob that
  does nothing. **Documented, not fixed:** the methodology no longer lists it
  among the functions producing the training-regimen result and now states that
  the reported regimen is onset-rate–independent, and `07_scope` carries it as
  an explicit non-modelled item. Wiring it in would move the published numbers,
  so it is a decision, not a cleanup — the paper's claim is now accurate either
  way.

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
- **Phase-6 honesty pass** — an adversarial audit found nine defects; each is
  now either made true, deleted, or stated as a named limitation:
  - `figures.py` imported nothing from `mission_results` and re-declared the
    station altitude, centrifuge profile, parking orbit and training caps as its
    own literals, so editing `config.yaml` moved every prose token and no
    figure. It plotted **eight** launch windows while the manuscript reported
    six. Figures now take a params dict, resolve it through the one config
    reader and call the canonical factories; `test_figures.py` counts the bars
    actually drawn against `ORBIT_WINDOW_COUNT` and parses the module for
    numeric constants.
  - `ORBIT_WINDOW_COUNT` was `len(launch_windows(..., num_windows=6))` — an
    input echoed back as a result, with no horizon and no filter. There is now a
    real `windows_in_horizon` filter and a `launch_horizon_h` knob; the count
    falls with altitude, rises with the horizon, and can be zero.
  - `TestConfigKnobsAreConsumed` claimed to flip every knob and tested four of
    twenty-three. It is now parametrised over all of `MISSION_DEFAULTS`, with a
    probe table that must cover the parameter set exactly.
  - `compute_transfer` passed a variable named `wet_mass` into a parameter named
    `dry_mass_kg`, and the +5400 kg basis appeared in no token — so the
    published 238.2 kg could not be re-derived from published numbers. The mass
    basis is now named `burnout_mass_kg`, published as
    `TRANSFER_BURNOUT_MASS_KG`, explained in the methodology, and pinned by a
    hand-arithmetic test.
  - `SHUTTLE_CRITICAL_PATH` rendered a seven-name union of **two** distinct
    57-minute paths as one "critical path", two of whose consecutive members are
    not dependency-linked. `TimelineSchedule` now carries `critical_activities`
    (the set) and `critical_chains` (the enumerated paths), and §Results reports
    both and says which is which.
  - `DRAX_CRASH_OPTIONS` hand-duplicated all eight durations and every edge of
    `DRAX_HIJACK_TIMELINE` with nothing comparing them, while the manuscript
    subtracted across the two copies. It is now derived from the timeline, with
    only the crash economics authored separately and a guard that refuses any
    coverage mismatch.
  - `test_figures.py::test_profile_plotted` asserted `isinstance(p, TrainingProfile)`
    — true by the constructor's return type, binding nothing. Replaced by
    content tests on the built figures.
  - `test_z_generate_allow_draft_without_outputs` ran where the outputs already
    existed, so its named precondition was false. It now runs in an isolated
    tree with a strict-mode negative control.
  - The methodology listed `gor_tolerance_multiplier` as one of three functions
    producing the training-regimen result; nothing consumes it. The claim is
    corrected and the limitation named (see Open, above).

## Notes

- `output/` is git-ignored and regenerable; `scripts/run_mission.py` restores a
  byte-identical tree on re-run.
- Measured coverage and test counts: `docs/_generated/COUNTS.md`. Do not quote
  them elsewhere in prose.
