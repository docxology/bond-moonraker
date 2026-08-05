"""DRAX mission adapter — the frozen BOND-API ``MissionProvider`` for moonraker.

Implements the canonical, FROZEN :class:`bond_api.protocol.MissionProvider`
protocol (see the BOND-API phase-1 contract). The provider is the thin adapter
between the BOND suite protocol and the pure, infrastructure-free domain core:
:mod:`moonraker.shuttle_ops` and :mod:`moonraker.schedule_crashing` (the hijack
timeline), :mod:`moonraker.orbital_logistics`, :mod:`moonraker.orbital_transfer`
and :mod:`moonraker.rendezvous` (the station and its resupply), and
:mod:`moonraker.centrifuge` with :mod:`moonraker.centrifuge_training` (the
g-force programme). The numeric work itself is delegated to the canonical
factories in :mod:`moonraker.mission_results`, so an outcome and its manuscript
token can never disagree.

The provider is deterministic: a fixed seed, no wall-clock dependence in its
provenance (``wall_time_s=0.0``), and an ``input_hash`` that is a stable SHA-256
over the serialized plan and package identity. Gadgets (the real domain
functions) are registered with :class:`bond_api.registry.GadgetRegistry` so the
orchestrator can discover them.

Discovery contract: a film package is a top-level module named by its slug
exposing ``mission.MissionProvider``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

__all__ = ["FILM", "CODENAME", "GADGETS", "MissionProvider", "PROVIDER", "provider"]

#: Package identity consumed by provenance and the orchestrator.
FILM = "moonraker"
CODENAME = "DRAX"
_PACKAGE_VERSION = "0.2.0"
_SEED = 23

#: Re-exported alongside the module for the orchestrator's convenience.
__version__ = _PACKAGE_VERSION

#: Module-level gadget registry (real callables, never mocks).
GADGETS = GadgetRegistry()


def _input_hash(plan: MissionPlan) -> str:
    """Stable SHA-256 over the plan and package identity (deterministic)."""
    payload = {
        "film": FILM,
        "package_version": _PACKAGE_VERSION,
        "seed": _SEED,
        "steps": [(step.name, step.action, step.params) for step in plan.steps],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class MissionProvider:  # noqa: N801 — name fixed by the discovery contract
    """Deterministic BOND-API provider modelling the DRAX hijack mission.

    The five lifecycle stages are pure functions of the domain core; the
    provider holds no state, so repeated runs are byte-identical.
    """

    film = FILM
    codename = CODENAME

    def brief(self) -> MissionBrief:
        """Declare the DRAX mission: six concepts, deterministic constraints."""
        return MissionBrief(
            film=self.film,
            codename=self.codename,
            objectives=(
                "model the shuttle hijack as a critical-path timeline",
                "solve Drax station orbital logistics",
                "certify a centrifuge g-force training profile",
                "size the Hohmann resupply transfer and propellant",
                "plan the centrifuge training regimen under exposure caps",
                "crash the hijack timeline to a tighter deadline at minimum cost",
            ),
            assets=(
                Asset(
                    kind="manifest",
                    name="timeline",
                    payload={"source": "shuttle_ops", "network": "DRAX_HIJACK_TIMELINE"},
                ),
                Asset(
                    kind="manifest",
                    name="orbit",
                    payload={"source": "orbital_logistics", "altitude_km": 350.0},
                ),
                Asset(
                    kind="manifest",
                    name="centrifuge",
                    payload={"source": "centrifuge", "radius_m": 8.0},
                ),
                Asset(
                    kind="manifest",
                    name="transfer",
                    payload={"source": "orbital_transfer", "park_altitude_km": 200.0},
                ),
                Asset(
                    kind="manifest",
                    name="training",
                    payload={"source": "centrifuge_training", "weekly_cap_g_s": 400.0},
                ),
                Asset(
                    kind="manifest",
                    name="crash",
                    payload={"source": "schedule_crashing", "deadline_min": 50.0},
                ),
            ),
            constraints=(
                Constraint(
                    kind="determinism", detail="fixed seed, no random draws, no external calls"
                ),
                Constraint(
                    kind="integrity", detail="input_hash auditable without re-running the film"
                ),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request goal against the available manifests.

        The findings are a deterministic snapshot of what the domain core can
        answer for the requested objective.
        """
        findings = [
            Finding(label="goal", detail=request.goal),
            Finding(label="timeline", detail="critical-path model over 8 hijack phases"),
            Finding(label="orbit", detail="Kepler period + launch-window + consumables model"),
            Finding(
                label="centrifuge", detail="ramp/sustain/decay profile with tolerance envelope"
            ),
            Finding(
                label="transfer",
                detail="Hohmann transfer, rocket-equation propellant and deorbit burn",
            ),
            Finding(label="training", detail="g·s exposure caps and weekly regimen planning"),
            Finding(label="crash", detail="minimum-cost time-cost crashing of the timeline"),
        ]
        return ReconReport(findings=tuple(findings))

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the six computation steps the mission must execute."""
        return MissionPlan(
            steps=(
                Step(
                    name="shuttle_timeline",
                    action="critical_path",
                    params={"deadline_min": 60.0, "network": "DRAX_HIJACK_TIMELINE"},
                ),
                Step(
                    name="orbital_windows",
                    action="launch_windows",
                    params={"altitude_km": 350.0, "num_windows": 6},
                ),
                Step(
                    name="centrifuge",
                    action="g_profile",
                    params={"target_g": 6.0, "radius_m": 8.0, "sustain_s": 12.0},
                ),
                Step(
                    name="rendezvous_transfer",
                    action="hohmann_transfer",
                    params={
                        "park_altitude_km": 200.0,
                        "station_altitude_km": 350.0,
                        "transfer_isp_s": 300.0,
                        "transfer_dry_mass_kg": 2500.0,
                    },
                ),
                Step(
                    name="training_cycle",
                    action="training_cycle",
                    params={
                        "sessions_per_week": 4,
                        "daily_cap_g_s": 150.0,
                        "weekly_cap_g_s": 400.0,
                    },
                ),
                Step(
                    name="schedule_crash",
                    action="schedule_crash",
                    params={"deadline_min": 50.0},
                ),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the plan over the real domain core and return full provenance.

        The computation branch on ``step.action`` runs the matching pure-domain
        algorithm and accumulates its metrics into ``results``. Every branch
        resolves its inputs from :data:`~moonraker.mission_results.MISSION_DEFAULTS`
        overridden by ``step.params``, so a plan that varies a parameter varies
        the whole computation rather than only the part that happens to read it.

        Raises:
            ValueError: when a step names an action this provider cannot run.
                A silently-skipped step would inflate ``steps_completed`` and
                report a success that was never computed.
        """
        from .centrifuge import build_training_profile, profile_is_safe
        from .mission_results import (
            MISSION_DEFAULTS,
            compute_crash,
            compute_training,
            compute_transfer,
        )
        from .orbital_logistics import (
            circular_speed,
            consumables_days,
            launch_windows,
            orbital_period,
            orbits_per_day,
            sustainable_crew,
        )
        from .shuttle_ops import DRAX_HIJACK_TIMELINE, compute_timeline, timeline_feasibility

        results: dict[str, Any] = {"steps_completed": 0, "outputs": []}

        for step in plan.steps:
            params: dict[str, Any] = {**MISSION_DEFAULTS, **step.params}
            if step.action == "critical_path":
                schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
                feasible, margin = timeline_feasibility(schedule, float(params["deadline_min"]))
                results["timeline"] = {
                    "total_duration_min": schedule.total_duration_min,
                    "critical_path": list(schedule.critical_path),
                    "feasible": feasible,
                    "margin_min": margin,
                }
            elif step.action == "launch_windows":
                altitude = float(params["altitude_km"])
                windows = launch_windows(altitude, num_windows=int(params["num_windows"]))
                period = orbital_period(altitude)
                results["orbit"] = {
                    "period_s": period,
                    "speed_km_s": circular_speed(altitude),
                    "orbits_per_day": orbits_per_day(altitude),
                    "windows": [(w.open_s, w.close_s) for w in windows],
                    "consumables_days_crew": consumables_days(
                        float(params["capacity_kg"]),
                        int(params["crew"]),
                        float(params["rate_kg_per_person_day"]),
                    ),
                    "sustainable_crew": sustainable_crew(
                        float(params["capacity_kg"]),
                        float(params["resupply_interval_days"]),
                        float(params["rate_kg_per_person_day"]),
                    ),
                }
            elif step.action == "g_profile":
                radius_m = float(params["radius_m"])
                profile = build_training_profile(
                    target_g=float(params["target_g"]),
                    radius_m=radius_m,
                    sustain_s=float(params["sustain_s"]),
                    ramp_rate_g_per_s=float(params["ramp_rate_g_per_s"]),
                    decay_rate_g_per_s=float(params["decay_rate_g_per_s"]),
                )
                safe, metrics = profile_is_safe(
                    profile,
                    g_limit=float(params["g_limit"]),
                    duration_limit_s=float(params["duration_limit_s"]),
                )
                results["centrifuge"] = {
                    "peak_g": profile.peak_g,
                    "sustain_s": profile.sustain_duration_s,
                    "safe": safe,
                    "allowable_s": metrics["allowable_s"],
                    "rpm": _rpm_for(profile.peak_g, radius_m),
                }
            elif step.action == "hohmann_transfer":
                results["transfer"] = compute_transfer(params)
            elif step.action == "training_cycle":
                results["training"] = compute_training(params)
            elif step.action == "schedule_crash":
                results["crash"] = compute_crash(params)
            else:
                raise ValueError(
                    f"step {step.name!r} names unknown action {step.action!r}; "
                    "moonraker cannot execute it"
                )
            results["steps_completed"] += 1
            results["outputs"].append(step.name)

        return MissionOutcome(
            success=bool(results.get("timeline", {}).get("feasible", False)),
            results=results,
            provenance=Provenance(
                package_version=_PACKAGE_VERSION,
                seed=_SEED,
                input_hash=_input_hash(plan),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record the DRAX standing lessons."""
        orbit = outcome.results.get("orbit", {})
        transfer = outcome.results.get("transfer", {})
        training = outcome.results.get("training", {})
        return Debrief(
            outcome=outcome,
            lessons=(
                "a hijack timeline is only as good as its critical path",
                "station logistics bind crew size, stock and launch cadence",
                "centrifuge profiles must respect the g-duration tolerance envelope",
                "resupply propellant follows the rocket equation, not guesswork",
                "training exposure caps bound the weekly regimen",
                "a tightened deadline has a minimum crash cost",
                f"orbit period {orbit.get('period_s', 'n/a')} s — deterministic",
                f"transfer Δv {transfer.get('total_dv_km_s', 'n/a')} km/s",
                f"training feasible: {training.get('feasible', 'n/a')}",
            ),
        )


def _rpm_for(g: float, radius_m: float) -> float:
    """Small local helper mapping peak-g back to centrifuge RPM."""
    from .centrifuge import rpm_for_g

    return rpm_for_g(g, radius_m)


#: Convenience singleton so scripts and the orchestrator can grab a provider.
PROVIDER = MissionProvider()


def provider() -> MissionProvider:
    """Return a fresh DRAX mission provider."""
    return MissionProvider()


def _register_gadgets() -> None:
    """Register the real domain callables as moonraker gadgets."""
    from .centrifuge import build_training_profile, max_sustained_duration, profile_is_safe
    from .centrifuge_training import plan_training_cycle, profile_exposure
    from .orbital_logistics import launch_windows, orbital_period, sustainable_crew
    from .orbital_transfer import (
        deorbit_dv,
        hohmann_transfer,
        phase_wait_time,
        propellant_mass,
        tsiolkovsky_mass_ratio,
    )
    from .rendezvous import single_impulse_intercept
    from .schedule_crashing import crash_schedule
    from .shuttle_ops import compute_timeline, timeline_feasibility

    GADGETS.register(
        FILM,
        {
            "compute_timeline": compute_timeline,
            "timeline_feasibility": timeline_feasibility,
            "launch_windows": launch_windows,
            "orbital_period": orbital_period,
            "sustainable_crew": sustainable_crew,
            "build_training_profile": build_training_profile,
            "max_sustained_duration": max_sustained_duration,
            "profile_is_safe": profile_is_safe,
            "hohmann_transfer": hohmann_transfer,
            "phase_wait_time": phase_wait_time,
            "tsiolkovsky_mass_ratio": tsiolkovsky_mass_ratio,
            "propellant_mass": propellant_mass,
            "deorbit_dv": deorbit_dv,
            "single_impulse_intercept": single_impulse_intercept,
            "plan_training_cycle": plan_training_cycle,
            "profile_exposure": profile_exposure,
            "crash_schedule": crash_schedule,
        },
    )


_register_gadgets()
