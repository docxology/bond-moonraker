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
            "CENTRIFUGE_VERDICT",
            "CENTRIFUGE_EXCEEDANCE_S",
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

    def test_centrifuge_verdict_is_pinned_to_the_computation(self) -> None:
        """The DRAX plateau overruns its allowance — pin it so prose cannot drift.

        The manuscript renders this verdict through ``{{CENTRIFUGE_VERDICT}}``.
        If the model or the config ever flips it, this test fails first rather
        than the prose silently asserting the opposite of the token.
        """
        results = compute_mission_results()
        assert results["CENTRIFUGE_SAFE"] == "no"
        assert results["CENTRIFUGE_VERDICT"] == "not certified"
        assert results["CENTRIFUGE_EXCEEDANCE_S"] > 0
        assert results["CENTRIFUGE_ALLOWABLE_S"] < results["CENTRIFUGE_SUSTAIN_S"]

    def test_shorter_plateau_earns_certification(self) -> None:
        """Cutting the plateau under the allowance flips the verdict positive."""
        results = compute_mission_results({"centrifuge_sustain_s": 5.0})
        assert results["CENTRIFUGE_SAFE"] == "yes"
        assert results["CENTRIFUGE_VERDICT"] == "certified"
        assert results["CENTRIFUGE_EXCEEDANCE_S"] < 0

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


class TestConfigKnobsAreConsumed:
    """Every knob in ``MISSION_DEFAULTS`` must change a result when flipped.

    A parameter that is named but never read is worse than no parameter: it
    advertises control the model does not have.
    """

    def test_margin_fraction_moves_the_allowance(self) -> None:
        tight = compute_mission_results({"centrifuge_margin_fraction": 0.5})
        loose = compute_mission_results({"centrifuge_margin_fraction": 0.0})
        assert tight["CENTRIFUGE_ALLOWABLE_S"] < loose["CENTRIFUGE_ALLOWABLE_S"]

    def test_duration_limit_can_govern_the_allowance(self) -> None:
        """Dropping the procedural ceiling below the envelope must bind it."""
        base = compute_mission_results()
        clamped = compute_mission_results({"duration_limit_s": 3.0})
        assert clamped["CENTRIFUGE_ALLOWABLE_S"] == pytest.approx(3.0)
        assert clamped["CENTRIFUGE_ALLOWABLE_S"] < base["CENTRIFUGE_ALLOWABLE_S"]

    def test_g_limit_rejects_on_peak(self) -> None:
        results = compute_mission_results({"g_limit": 5.0, "centrifuge_sustain_s": 1.0})
        assert results["CENTRIFUGE_SAFE"] == "no"

    def test_isp_moves_the_propellant_budget(self) -> None:
        efficient = compute_mission_results({"transfer_isp_s": 450.0})
        thirsty = compute_mission_results({"transfer_isp_s": 200.0})
        assert efficient["TRANSFER_PROPELLANT_KG"] < thirsty["TRANSFER_PROPELLANT_KG"]
