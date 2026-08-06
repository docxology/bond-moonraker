"""Tests for moonraker.mission — the frozen BOND-API MissionProvider adapter."""

from __future__ import annotations

import pytest
from bond_api.discovery import load_provider
from bond_api.protocol import MissionProvider as ProtocolMissionProvider
from bond_api.protocol import ReconRequest, run_mission

from moonraker.mission import FILM, GADGETS, PROVIDER, MissionProvider, provider


class TestProviderSurface:
    def test_is_runtime_checkable_protocol(self) -> None:
        assert isinstance(PROVIDER, ProtocolMissionProvider)
        assert isinstance(provider(), ProtocolMissionProvider)

    def test_identity(self) -> None:
        assert PROVIDER.film == FILM == "moonraker"
        assert PROVIDER.codename == "DRAX"

    def test_brief(self) -> None:
        brief = PROVIDER.brief()
        assert brief.film == "moonraker"
        assert brief.codename == "DRAX"
        assert len(brief.objectives) == 6
        assert brief.assets
        assert brief.constraints

    def test_recon(self) -> None:
        report = PROVIDER.recon(ReconRequest("assess intercept"))
        assert report.findings
        assert report.findings[0].label == "goal"
        labels = {f.label for f in report.findings}
        assert {"transfer", "training", "crash"} <= labels

    def test_plan(self) -> None:
        plan = PROVIDER.plan(PROVIDER.brief())
        assert len(plan.steps) == 6
        actions = {s.action for s in plan.steps}
        assert {
            "critical_path",
            "launch_windows",
            "g_profile",
            "hohmann_transfer",
            "training_cycle",
            "schedule_crash",
        } == actions

    def test_execute_keys(self) -> None:
        outcome = PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))
        assert outcome.success is True
        for key in ("timeline", "orbit", "centrifuge", "transfer", "training", "crash"):
            assert key in outcome.results
        assert outcome.results["steps_completed"] == 6
        assert outcome.provenance.seed == 23
        assert outcome.provenance.wall_time_s == 0.0
        assert outcome.provenance.input_hash

    def test_execute_reports_activity_set_and_paths_separately(self) -> None:
        """The outcome must not present the zero-slack union as one route."""
        outcome = PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))
        timeline = outcome.results["timeline"]
        assert "critical_path" not in timeline
        assert len(timeline["critical_paths"]) == 2
        assert set(timeline["critical_activities"]) == {
            name for path in timeline["critical_paths"] for name in path
        }
        assert all(
            len(path) < len(timeline["critical_activities"]) for path in timeline["critical_paths"]
        )

    def test_debrief(self) -> None:
        outcome = PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))
        debrief = PROVIDER.debrief(outcome)
        assert debrief.lessons
        assert debrief.outcome is outcome


class TestDeterminism:
    def test_execute_byte_identical(self) -> None:
        p1 = PROVIDER.plan(PROVIDER.brief())
        p2 = PROVIDER.plan(PROVIDER.brief())
        o1 = PROVIDER.execute(p1)
        o2 = PROVIDER.execute(p2)
        assert o1.results == o2.results
        assert o1.provenance.input_hash == o2.provenance.input_hash

    def test_run_mission_full_flow(self) -> None:
        debrief = run_mission(PROVIDER, ReconRequest("full flow"))
        assert debrief.outcome.results["steps_completed"] == 6
        assert debrief.outcome.success is True


class TestGadgets:
    def test_gadgets_registered(self) -> None:
        names = GADGETS.gadgets_for(FILM)
        assert "compute_timeline" in names
        assert "launch_windows" in names
        assert "build_training_profile" in names
        assert "hohmann_transfer" in names
        assert "single_impulse_intercept" in names
        assert "plan_training_cycle" in names
        assert "crash_schedule" in names
        assert len(names) >= 16

    def test_gadgets_are_real_and_callable(self) -> None:
        timeline_fn = GADGETS.lookup(FILM, "compute_timeline")
        from moonraker.shuttle_ops import DRAX_HIJACK_TIMELINE

        schedule = timeline_fn(DRAX_HIJACK_TIMELINE)
        assert schedule.total_duration_min > 0.0


class TestDiscovery:
    def test_discoverable_by_slug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # load_provider imports '<slug>.mission' from sys.path; our package src/
        # is already on sys.path via conftest.
        found = load_provider("moonraker")
        assert found.film == "moonraker"


class TestProviderFactory:
    def test_fresh_provider(self) -> None:
        p = provider()
        assert isinstance(p, MissionProvider)
        assert p.film == "moonraker"


class TestUnknownAction:
    def test_unknown_action_raises_instead_of_silently_counting(self) -> None:
        """An unrunnable step must abort, not inflate ``steps_completed``.

        Silently skipping an unknown action would let the orchestrator read a
        successful outcome for a computation that never ran.
        """
        from bond_api.protocol import MissionPlan, Step

        plan = MissionPlan(steps=(Step(name="bogus", action="teleport", params={}),))
        with pytest.raises(ValueError, match="unknown action"):
            PROVIDER.execute(plan)


class TestPlanParametersAreHonoured:
    def test_centrifuge_radius_from_step_params(self) -> None:
        """The reported RPM must follow the step's arm radius, not a constant.

        A longer arm reaches the same g at a lower RPM; if the branch ignored
        ``radius_m`` both runs would report an identical figure.
        """
        from bond_api.protocol import MissionPlan, Step

        def _rpm(radius_m: float) -> float:
            plan = MissionPlan(
                steps=(
                    Step(
                        name="centrifuge",
                        action="g_profile",
                        params={"target_g": 6.0, "radius_m": radius_m, "sustain_s": 12.0},
                    ),
                )
            )
            rpm = PROVIDER.execute(plan).results["centrifuge"]["rpm"]
            assert isinstance(rpm, float)
            return rpm

        assert _rpm(16.0) < _rpm(8.0)

    def test_orbit_consumables_follow_step_params(self) -> None:
        """Doubling the delivered capacity must double the sustainable crew."""
        from bond_api.protocol import MissionPlan, Step

        def _crew(capacity_kg: float) -> int:
            plan = MissionPlan(
                steps=(
                    Step(
                        name="orbital_windows",
                        action="launch_windows",
                        params={
                            "altitude_km": 350.0,
                            "num_windows": 6,
                            "capacity_kg": capacity_kg,
                        },
                    ),
                )
            )
            crew = PROVIDER.execute(plan).results["orbit"]["sustainable_crew"]
            assert isinstance(crew, int)
            return crew

        assert _crew(10800.0) == 2 * _crew(5400.0)


class TestCanonicalStepParamsAreHonoured:
    """Plan-step parameters must be honoured end to end, not silently dropped.

    These pin the round-2 fixes for the executes' ``launch_windows`` and
    ``g_profile`` branches (and their siblings), which used to read short,
    non-canonical keys and drop a step that set the canonical name. Each branch
    now resolves through the canonical factories, so both the canonical spelling
    and the legacy alias move the computation.
    """

    def test_launch_windows_honours_station_altitude(self) -> None:
        from bond_api.protocol import MissionPlan, Step

        def _period(params: dict[str, float]) -> float:
            plan = MissionPlan(
                steps=(Step(name="orbital_windows", action="launch_windows", params=params),)
            )
            return PROVIDER.execute(plan).results["orbit"]["period_s"]

        base = _period({"station_altitude_km": 350.0})
        higher = _period({"station_altitude_km": 700.0})
        assert higher > base  # higher orbit -> longer Kepler period
        # The legacy short spelling must move it identically, not be dropped.
        assert _period({"altitude_km": 700.0}) == pytest.approx(higher)
        assert higher != pytest.approx(base)

    def test_launch_windows_reports_horizon_bounded_windows(self) -> None:
        """The adapter's window list is horizon-filtered, matching compute_orbit."""
        from bond_api.protocol import MissionPlan, Step

        plan = MissionPlan(
            steps=(Step(name="orbital_windows", action="launch_windows", params={}),)
        )
        windows = PROVIDER.execute(plan).results["orbit"]["windows"]
        assert windows  # non-empty under the shipped 4 h horizon
        for open_s, close_s in windows:
            assert close_s > open_s

    def test_centrifuge_margin_fraction_honoured_by_g_profile_step(self) -> None:
        """``allowable_s`` must follow the step's margin, under the published rule."""
        from bond_api.protocol import MissionPlan, Step

        from moonraker.mission_results import MISSION_DEFAULTS, compute_centrifuge

        def _allowable(margin: float) -> float:
            plan = MissionPlan(
                steps=(
                    Step(
                        name="centrifuge",
                        action="g_profile",
                        params={"centrifuge_margin_fraction": margin},
                    ),
                )
            )
            return PROVIDER.execute(plan).results["centrifuge"]["allowable_s"]

        tight = _allowable(0.5)
        loose = _allowable(0.0)
        assert tight < loose
        # Must equal the published factory under the same margin — same rule.
        merged = {**MISSION_DEFAULTS, "centrifuge_margin_fraction": 0.5}
        assert tight == pytest.approx(compute_centrifuge(merged)["allowable_s"])

    def test_schedule_crash_honours_canonical_deadline(self) -> None:
        from bond_api.protocol import MissionPlan, Step

        def _run(deadline: float) -> dict[str, object]:
            plan = MissionPlan(
                steps=(
                    Step(
                        name="crash",
                        action="schedule_crash",
                        params={"crash_deadline_min": deadline},
                    ),
                )
            )
            return PROVIDER.execute(plan).results["crash"]

        loose = _run(55.0)
        tight = _run(48.0)
        assert tight["feasible"] is True
        assert tight["saved_min"] > loose["saved_min"]  # type: ignore[operator]

    def test_training_cycle_honours_session_count(self) -> None:
        from bond_api.protocol import MissionPlan, Step

        def _weekly(sessions: int) -> float:
            plan = MissionPlan(
                steps=(
                    Step(
                        name="training",
                        action="training_cycle",
                        params={"training_sessions_per_week": sessions},
                    ),
                )
            )
            return PROVIDER.execute(plan).results["training"]["weekly_g_s"]

        assert _weekly(4) == pytest.approx(_weekly(2) * 2.0)
