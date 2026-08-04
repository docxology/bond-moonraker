"""Tests for moonraker.mission_results — the canonical result computation."""

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
        ):
            assert key in results

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
