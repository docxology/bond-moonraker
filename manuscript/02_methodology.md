# Methodology

All three models are deterministic and closed-form; parameter values are read
once from `manuscript/config.yaml` → `mission:` and shared by
`moonraker/mission_results.py` and `moonraker/manuscript_variables.py`.

## Shuttle hijack timeline (`shuttle_ops.py`)

The hijack is a set of `TimelineActivity` records — a name, a duration in
minutes, and prerequisite phases. `compute_timeline` runs the Critical Path
Method: a forward pass sets the earliest start of each activity to the maximum
earliest finish of its prerequisites; a backward pass sets the latest finish to
the minimum latest start of its successors. Total float (slack) is the
difference between late and early finishes; activities with zero slack form the
**critical path**. `timeline_feasibility` then checks the plan against the
shuttle's point of no return, {{CONFIG_DEADLINE_MIN}} minutes from launch.

## Space-station orbital logistics (`orbital_logistics.py`)

Kepler's third law gives the circular-orbit period
$T = 2\pi\sqrt{a^3/\mu}$ with $a = R_\oplus + h$; the circular speed is
$v = \sqrt{\mu/a}$. Orbits per day divide the sidereal day by $T$. Ground
launch windows open at each half-period plane crossing and stay open for the
usable pass at a minimum elevation (horizon geometry shrinks the visible
central angle). The consumables model is linear: `consumables_days = capacity /
(crew × per-capita daily rate)`, and `sustainable_crew` floors the largest
integer crew that survives the {{CONFIG_RESUPPLY_INTERVAL_DAYS}}-day resupply
cadence.

## Centrifuge g-force profiles (`centrifuge.py`)

Centripetal acceleration maps to g via $g = (2\pi\,\mathrm{rpm}/60)^2 r / g_0$.
`build_training_profile` produces a ramp → sustain → decay g-level trace. A
deterministic power-law tolerance envelope $t = \min(800\,g^{-2.5},\,60)$
bounds how long a peak g can be sustained, and `profile_is_safe` verifies the
profile never exceeds the {{CONFIG_TARGET_G}} g target and that its
{{CONFIG_SUSTAIN_S}} s plateau stays within the allowance (with a reserved
safety fraction).
