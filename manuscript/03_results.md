# Results

All numbers below are computed by `moonraker/mission_results.py` and injected
as tokens — the manuscript never hand-authors a metric. The consolidated table
collects the headline values; each is a live token whose resolved value appears
in `output/manuscript/03_results.md`.

| Concept | Metric | Value |
|---|---|---|
| Hijack timeline | Total duration | {{SHUTTLE_TOTAL_MIN}} min |
| Hijack timeline | Distinct critical paths | {{SHUTTLE_CRITICAL_PATH_COUNT}} |
| Crashed to deadline | Final duration | {{CRASH_FINAL_MIN}} min |
| Crashed to deadline | Minimum crash cost | {{CRASH_TOTAL_COST}} |
| Station | Orbital period | {{ORBIT_PERIOD_S}} s |
| Station | Usable windows ({{CONFIG_LAUNCH_HORIZON_H}} h) | {{ORBIT_WINDOW_COUNT}} |
| Station | Stores depletion | {{ORBIT_CONSUMABLES_DAYS}} days |
| Station | Sustainable crew (per cycle) | {{ORBIT_SUSTAINABLE_CREW}} |
| Transfer | Total Δv | {{TRANSFER_TOTAL_DV_KMS}} km/s |
| Transfer | Propellant | {{TRANSFER_PROPELLANT_KG}} kg |
| Rendezvous | Intercept impulse | {{RENDEZVOUS_IMPULSE_M_S}} m/s |
| Centrifuge | Peak / allowance | {{CENTRIFUGE_PEAK_G}} g / {{CENTRIFUGE_ALLOWABLE_S}} s |
| Centrifuge | Verdict / remediation | {{CENTRIFUGE_VERDICT}} / {{REMEDIATION_VERDICT}} |
| Training | Sessions admitted per week | {{TRAINING_RECOMMENDED}} |

## Shuttle hijack timeline

The hijack finishes in **{{SHUTTLE_TOTAL_MIN}} minutes** over
**{{SHUTTLE_NUM_PHASES}} phases**. The network carries
**{{SHUTTLE_CRITICAL_PATH_COUNT}}** distinct critical paths, each
{{SHUTTLE_TOTAL_MIN}} minutes long: **{{SHUTTLE_CRITICAL_PATHS}}**. Their union
— the load-bearing, zero-slack activity set — is
**{{SHUTTLE_CRITICAL_ACTIVITIES}}**. That set is *not* itself a route: two of
its consecutive members are on different paths and are not linked by any
dependency, so delaying any one of them delays the mission while only the
listed paths can be walked end to end. Against the
{{CONFIG_DEADLINE_MIN}}-minute point of no return the plan is
**{{SHUTTLE_FEASIBLE}}**, with a margin of **{{SHUTTLE_MARGIN_MIN}} minutes**.

![The shuttle-hijack critical-path Gantt chart.](../output/figures/timeline_critical_path.png){#fig:timeline}

If the operation must complete in **{{CRASH_DEADLINE_MIN}} minutes**, schedule
crashing compresses the plan to **{{CRASH_FINAL_MIN}} minutes** — saving
**{{CRASH_SAVED_MIN}} minutes** — at a minimum cost of **{{CRASH_TOTAL_COST}}**
by crashing **{{CRASH_ACTIVITIES}}**. The saving is a subtraction within one
network: the crashable model reads its durations and dependency edges from the
same `DRAX_HIJACK_TIMELINE` that produced the {{SHUTTLE_TOTAL_MIN}}-minute
total, adding only the per-activity crash limit and cost.

## Space-station orbital logistics

The DRAX station at {{CONFIG_STATION_ALTITUDE_KM}} km altitude has an orbital
period of **{{ORBIT_PERIOD_S}} s**, a circular speed of
**{{ORBIT_SPEED_KMS}} km/s**, and completes **{{ORBIT_ORBITS_PER_DAY}}**
orbits per sidereal day. Over a {{CONFIG_LAUNCH_HORIZON_H}}-hour launch
planning horizon, **{{ORBIT_WINDOW_COUNT}}** ground launch windows both open
and close in time to be usable — the count is the horizon divided by the
half-period after allowing for one full pass, not a requested number: raising
the station lengthens the period and drops the count, and a horizon shorter
than a single pass admits none. With
{{CONFIG_CAPACITY_KG}} kg of consumables delivered and a per-capita rate of
{{CONFIG_RATE_KG_PERSON_DAY}} kg/person/day, the stores last
**{{ORBIT_CONSUMABLES_DAYS}} days** — the depletion horizon for the configured
{{CONFIG_CREW}} crew — and a single resupply can sustain up to
**{{ORBIT_SUSTAINABLE_CREW}}** people for the {{CONFIG_RESUPPLY_INTERVAL_DAYS}}-day
cadence. That last figure is a **per-cycle logistics ceiling, not a
habitability claim**: it is capacity divided by (cadence × per-capita rate),
and the station's own crew is the far smaller {{CONFIG_CREW}}. It is also
deliberately distinct from the {{ORBIT_CONSUMABLES_DAYS}}-day stores figure:
the two only coincide at the shipped cadence and crew.

![Orbital period versus altitude with the DRAX station's launch windows.](../output/figures/orbit_period_windows.png){#fig:orbit}

### Resupply transfer and rendezvous

Flying from the {{CONFIG_PARK_ALTITUDE_KM}}-km parking orbit up to the station
with a Hohmann transfer costs **{{TRANSFER_DV1_KMS}} + {{TRANSFER_DV2_KMS}} =
{{TRANSFER_TOTAL_DV_KMS}} km/s**, over a **{{TRANSFER_TIME_MIN}}-minute**
half-ellipse. The chaser must wait **{{TRANSFER_WAIT_H}} h** for the
**{{TRANSFER_LEAD_DEG}}°** lead angle. On a {{CONFIG_TRANSFER_ISP_S}} s engine
the rocket equation gives a mass ratio of **{{TRANSFER_MASS_RATIO}}**. The mass
that ratio acts on is the **burnout** mass — what the craft still weighs when
the second burn ends — which here is
**{{TRANSFER_BURNOUT_MASS_KG}} kg**: the {{CONFIG_TRANSFER_DRY_MASS_KG}} kg dry
structure *plus* the {{CONFIG_CAPACITY_KG}} kg of consumables, since the cargo
is delivered after circularisation and is therefore accelerated by both burns.
So the propellant is
{{TRANSFER_BURNOUT_MASS_KG}} × ({{TRANSFER_MASS_RATIO}} − 1) =
**{{TRANSFER_PROPELLANT_KG}} kg**; deorbit adds
**{{TRANSFER_DEORBIT_KMS}} km/s**. The final
Clohessy–Wiltshire approach needs a **{{RENDEZVOUS_IMPULSE_M_S}} m/s**
corrective impulse over **{{RENDEZVOUS_TIME_S}} s**.

![The Hohmann resupply transfer geometry.](../output/figures/hohmann_transfer.png){#fig:hohmann}

## Centrifuge g-force profile and training regimen

A **{{CENTRIFUGE_PEAK_G}} g** run on an {{CONFIG_CENTRIFUGE_RADIUS_M}} m arm
demands about **{{CENTRIFUGE_RPM}} rpm**. The governing allowance at that peak
is **{{CENTRIFUGE_ALLOWABLE_S}} s** — the +Gz tolerance envelope derated by the
{{CONFIG_MARGIN_PCT}}% safety margin, which here is tighter than the
{{CONFIG_DURATION_LIMIT_S}} s procedural ceiling. The DRAX profile's
{{CONFIG_SUSTAIN_S}} s plateau therefore overruns the allowance by
**{{CENTRIFUGE_EXCEEDANCE_S}} s**, and the run is **{{CENTRIFUGE_VERDICT}}**
(``CENTRIFUGE_SAFE = {{CENTRIFUGE_SAFE}}``).

This is a substantive negative result, not a modelling artefact: the shooting
script's training sequence is *outside* the survivable envelope this package
computes, and the model reports so rather than being tuned until it agrees.
The remediation the model implies is itself computed, not inferred: holding the
plateau at **{{REMEDIATION_SUSTAIN_S}} s** — cutting
**{{REMEDIATION_REDUCTION_S}} s** from the {{CONFIG_SUSTAIN_S}} s plateau —
yields a **{{REMEDIATION_VERDICT}}** run
(``REMEDIATION_SAFE = {{REMEDIATION_SAFE}}``) under the same tolerance and
procedural ceilings. `tests/test_mission_results.py` pins both the failing
verdict and the certification of this remediated profile, so this paragraph
cannot drift away from the computation.

Each session accumulates
**{{TRAINING_PER_SESSION_GS}} g·s** of exposure; under the
{{CONFIG_TRAINING_DAILY_CAP_GS}} g·s daily and
{{CONFIG_TRAINING_WEEKLY_CAP_GS}} g·s weekly caps, the
**{{TRAINING_SESSIONS}}-session** weekly programme is
**{{TRAINING_FEASIBLE}}**, and the caps admit **{{TRAINING_RECOMMENDED}}**
sessions per week.

![The centrifuge g-level profile with the g-duration tolerance envelope.](../output/figures/centrifuge_g_profile.png){#fig:centrifuge}

![Weekly centrifuge training load against the exposure caps.](../output/figures/training_weekly_load.png){#fig:training}
