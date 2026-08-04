# Results

All numbers below are computed by `moonraker/mission_results.py` and injected
as tokens — the manuscript never hand-authors a metric.

## Shuttle hijack timeline

The hijack finishes in **{{SHUTTLE_TOTAL_MIN}} minutes** over
**{{SHUTTLE_NUM_PHASES}} phases**. The load-bearing critical path is
**{{SHUTTLE_CRITICAL_PATH}}**. Against the {{CONFIG_DEADLINE_MIN}}-minute point
of no return the plan is **{{SHUTTLE_FEASIBLE}}**, with a margin of
**{{SHUTTLE_MARGIN_MIN}} minutes**.

![The shuttle-hijack critical-path Gantt chart.](../output/figures/timeline_critical_path.png){#fig:timeline}

If the operation must complete in **{{CRASH_DEADLINE_MIN}} minutes**, schedule
crashing compresses the plan to **{{CRASH_FINAL_MIN}} minutes** — saving
**{{CRASH_SAVED_MIN}} minutes** — at a minimum cost of **{{CRASH_TOTAL_COST}}**
by crashing **{{CRASH_ACTIVITIES}}**.

## Space-station orbital logistics

The DRAX station at {{CONFIG_STATION_ALTITUDE_KM}} km altitude has an orbital
period of **{{ORBIT_PERIOD_S}} s**, a circular speed of
**{{ORBIT_SPEED_KMS}} km/s**, and completes **{{ORBIT_ORBITS_PER_DAY}}**
orbits per sidereal day. The planning horizon yields
**{{ORBIT_WINDOW_COUNT}}** usable ground launch windows. With
{{CONFIG_CAPACITY_KG}} kg of consumables delivered and a per-capita rate of
{{CONFIG_RATE_KG_PERSON_DAY}} kg/person/day, the stores last
**{{ORBIT_CONSUMABLES_DAYS}} days** and sustain **{{ORBIT_SUSTAINABLE_CREW}}**
crew on the {{CONFIG_RESUPPLY_INTERVAL_DAYS}}-day resupply cadence.

![Orbital period versus altitude with the DRAX station's launch windows.](../output/figures/orbit_period_windows.png){#fig:orbit}

### Resupply transfer and rendezvous

Flying from the {{CONFIG_PARK_ALTITUDE_KM}}-km parking orbit up to the station
with a Hohmann transfer costs **{{TRANSFER_DV1_KMS}} + {{TRANSFER_DV2_KMS}} =
{{TRANSFER_TOTAL_DV_KMS}} km/s**, over a **{{TRANSFER_TIME_MIN}}-minute**
half-ellipse. The chaser must wait **{{TRANSFER_WAIT_H}} h** for the
**{{TRANSFER_LEAD_DEG}}°** lead angle. On a {{CONFIG_TRANSFER_ISP_S}} s engine
the rocket equation gives a mass ratio of **{{TRANSFER_MASS_RATIO}}**, i.e.
**{{TRANSFER_PROPELLANT_KG}} kg** of propellant for the loaded resupply craft;
deorbit adds **{{TRANSFER_DEORBIT_KMS}} km/s**. The final
Clohessy–Wiltshire approach needs a **{{RENDEZVOUS_IMPULSE_M_S}} m/s**
corrective impulse over **{{RENDEZVOUS_TIME_S}} s**.

![The Hohmann resupply transfer geometry.](../output/figures/hohmann_transfer.png){#fig:hohmann}

## Centrifuge g-force profile and training regimen

A **{{CENTRIFUGE_PEAK_G}} g** run on an {{CONFIG_CENTRIFUGE_RADIUS_M}} m arm
demands about **{{CENTRIFUGE_RPM}} rpm**. Holding the
{{CONFIG_SUSTAIN_S}} s plateau is **{{CENTRIFUGE_SAFE}}** given an allowable
sustained duration of **{{CENTRIFUGE_ALLOWABLE_S}} s** at peak g — comfortably
inside the tolerance envelope. Each session accumulates
**{{TRAINING_PER_SESSION_GS}} g·s** of exposure; under the
{{CONFIG_TRAINING_DAILY_CAP_GS}} g·s daily and
{{CONFIG_TRAINING_WEEKLY_CAP_GS}} g·s weekly caps, the
**{{TRAINING_SESSIONS}}-session** weekly programme is
**{{TRAINING_FEASIBLE}}**, and the caps admit **{{TRAINING_RECOMMENDED}}**
sessions per week.

![The centrifuge g-level profile with the g-duration tolerance envelope.](../output/figures/centrifuge_g_profile.png){#fig:centrifuge}

![Weekly centrifuge training load against the exposure caps.](../output/figures/training_weekly_load.png){#fig:training}
