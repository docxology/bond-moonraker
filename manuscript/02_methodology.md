# Methodology

All models are deterministic and closed-form; parameter values are read once
from `manuscript/config.yaml` → `mission:` and shared by
`moonraker/mission_results.py` and `moonraker/manuscript_variables.py`.

## Shuttle hijack timeline (`shuttle_ops.py`)

The hijack is a set of `TimelineActivity` records — a name, a duration in
minutes, and prerequisite phases. `compute_timeline` runs the Critical Path
Method: a forward pass sets the earliest start of each activity to the maximum
earliest finish of its prerequisites; a backward pass sets the latest finish to
the minimum latest start of its successors. Total float (slack) is the
difference between late and early finishes; activities with zero slack form the
**critical path**. `timeline_feasibility` checks the plan against the shuttle's
point of no return, {{CONFIG_DEADLINE_MIN}} minutes from launch.

**Time-cost crashing** (`schedule_crashing.py`) compresses the timeline when
the deadline tightens. Every `CrashableActivity` carries a normal duration, a
minimum (crashed) duration and a linear cost per minute saved.
`crash_schedule` runs the classic greedy crash: it re-solves the CPM, picks the
cheapest still-crashable activity on the current critical path, and crashes it
one minute at a time until the deadline is met or compression is exhausted.

## Space-station orbital logistics (`orbital_logistics.py`)

Kepler's third law gives the circular-orbit period $T = 2\pi\sqrt{a^3/\mu}$
with $a = R_\oplus + h$; the circular speed is $v = \sqrt{\mu/a}$. Orbits per
day divide the sidereal day by $T$. Ground launch windows open at each
half-period plane crossing and stay open for the usable pass at a minimum
elevation. The consumables model is linear: `consumables_days = capacity /
(crew × per-capita rate)`, and `sustainable_crew` floors the largest crew that
survives the {{CONFIG_RESUPPLY_INTERVAL_DAYS}}-day resupply cadence.

**Orbital transfer** (`orbital_transfer.py`) flies the resupply from a
{{CONFIG_PARK_ALTITUDE_KM}}-km parking orbit up to the station with the
Hohmann transfer: two tangential burns sized by the vis-viva equation
$v = \sqrt{\mu(2/r - 1/a)}$, a half-ellipse transfer time
$t = \pi\sqrt{a^3/\mu}$ [@hohmann1925], and a deterministic phase-wait that
aligns the chaser to the target's lead angle. The rocket equation
$m_0/m_f = \exp(\Delta v/(I_{\text{sp}} g_0))$ [@tsiolkovsky1903] sizes the
propellant; a retrograde burn drops the perigee for deorbit.

**Rendezvous guidance** (`rendezvous.py`) models the final approach in the
station's local-vertical/local-horizontal frame with the linearised
Clohessy–Wiltshire equations [@clohessy1960]. `cw_propagate` propagates the
relative state and `single_impulse_intercept` solves for the single corrective
impulse that zeroes the relative position at a chosen time (raising on the
geometric singularities where a single-impulse transfer is impossible).

## Centrifuge g-force profiles (`centrifuge.py`)

Centripetal acceleration maps to g via $g = (2\pi\,\mathrm{rpm}/60)^2 r / g_0$.
`build_training_profile` produces a ramp → sustain → decay g-level trace; a
deterministic power-law tolerance envelope
$t = \min(800\,g^{-2.5},\,60)$ bounds the sustainable duration, and
`profile_is_safe` verifies the {{CONFIG_TARGET_G}} g profile with its
{{CONFIG_SUSTAIN_S}} s plateau stays inside the allowance.

**Training regimen** (`centrifuge_training.py`) doses the programme in g·s:
`profile_exposure` integrates the +Gz exposure above baseline,
`gor_tolerance_multiplier` scales tolerance with the gradual-onset rate (slower
onset → longer tolerated time), and `plan_training_cycle` enforces daily and
weekly exposure caps to return the sustainable session count — a regimen
bounded by the physiology of +Gz tolerance [@burton1988].
