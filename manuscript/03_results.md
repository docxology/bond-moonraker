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

## Centrifuge g-force profile

A **{{CENTRIFUGE_PEAK_G}} g** run on an {{CONFIG_CENTRIFUGE_RADIUS_M}} m arm
demands about **{{CENTRIFUGE_RPM}} rpm**. Holding the
{{CONFIG_SUSTAIN_S}} s plateau is **{{CENTRIFUGE_SAFE}}** given an allowable
sustained duration of **{{CENTRIFUGE_ALLOWABLE_S}} s** at peak g — comfortably
inside the tolerance envelope.

![The centrifuge g-level profile with the g-duration tolerance envelope.](../output/figures/centrifuge_g_profile.png){#fig:centrifuge}
