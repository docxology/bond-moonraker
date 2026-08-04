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
