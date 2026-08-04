"""Tests for moonraker.mission_results — the canonical result computation."""

import pytest

from moonraker.mission_results import MISSION_DEFAULTS, compute_mission_results


class TestComputeMissionResults:
    def test_returns_full_metric_set(self) -> None:
        results = compute_mission_results()
        for key in (
            "SHUTTLE_TOTAL_MIN",
            "SHUTTLE_NUM_PHASES",
            "SHUTTLE_CRITICAL_PATH",
            "SHUTTLE_FEASIBLE",
            "SHUTTLE_MARGIN_MIN",
            "ORBIT_PERIOD_S",
            "ORBIT_SPEED_KMS",
            "ORBIT_ORBITS_PER_DAY",
            "ORBIT_WINDOW_COUNT",
            "ORBIT_CONSUMABLES_DAYS",
            "ORBIT_SUSTAINABLE_CREW",
            "CENTRIFUGE_PEAK_G",
            "CENTRIFUGE_SUSTAIN_S",
            "CENTRIFUGE_ALLOWABLE_S",
            "CENTRIFUGE_RPM",
            "CENTRIFUGE_SAFE",
            "TRANSFER_DV1_KMS",
            "TRANSFER_DV2_KMS",
            "TRANSFER_TOTAL_DV_KMS",
            "TRANSFER_TIME_MIN",
            "TRANSFER_WAIT_H",
            "TRANSFER_LEAD_DEG",
            "TRANSFER_MASS_RATIO",
            "TRANSFER_PROPELLANT_KG",
            "TRANSFER_DEORBIT_KMS",
            "RENDEZVOUS_IMPULSE_M_S",
            "RENDEZVOUS_TIME_S",
            "TRAINING_PER_SESSION_GS",
            "TRAINING_WEEKLY_GS",
            "TRAINING_SESSIONS",
            "TRAINING_RECOMMENDED",
            "TRAINING_FEASIBLE",
            "CRASH_DEADLINE_MIN",
            "CRASH_FINAL_MIN",
            "CRASH_SAVED_MIN",
            "CRASH_TOTAL_COST",
            "CRASH_FEASIBLE",
            "CRASH_ACTIVITIES",
        ):
            assert key in results

    def test_deepened_values(self) -> None:
        results = compute_mission_results()
        assert results["TRANSFER_TOTAL_DV_KMS"] == pytest.approx(0.0874)
        assert results["CRASH_FINAL_MIN"] == pytest.approx(50.0)
        assert results["TRAINING_FEASIBLE"] == "yes"
        assert results["TRAINING_RECOMMENDED"] == 4
        assert results["RENDEZVOUS_IMPULSE_M_S"] == pytest.approx(1.875)

    def test_defaults_feasible(self) -> None:
        results = compute_mission_results()
        assert results["SHUTTLE_FEASIBLE"] == "yes"
        assert results["SHUTTLE_MARGIN_MIN"] > 0

    def test_deterministic(self) -> None:
        assert compute_mission_results() == compute_mission_results()

    def test_param_override(self) -> None:
        # A shorter deadline flips the shuttle plan infeasible.
        results = compute_mission_results({"deadline_min": 30.0})
        assert results["SHUTTLE_FEASIBLE"] == "no"
        assert results["SHUTTLE_MARGIN_MIN"] < 0

    def test_defaults_are_complete(self) -> None:
        assert "capacity_kg" in MISSION_DEFAULTS
        assert "station_altitude_km" in MISSION_DEFAULTS
