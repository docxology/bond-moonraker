"""Tests for moonraker.mission_results — the canonical result computation."""

import pytest

from moonraker.mission_results import MISSION_DEFAULTS, compute_mission_results


class TestComputeMissionResults:
    def test_returns_full_metric_set(self) -> None:
        results = compute_mission_results()
        for key in (
            "SHUTTLE_TOTAL_MIN",
            "SHUTTLE_NUM_PHASES",
            "SHUTTLE_CRITICAL_ACTIVITIES",
            "SHUTTLE_CRITICAL_PATHS",
            "SHUTTLE_CRITICAL_PATH_COUNT",
            "SHUTTLE_FEASIBLE",
            "SHUTTLE_MARGIN_MIN",
            "ORBIT_PERIOD_S",
            "ORBIT_SPEED_KMS",
            "ORBIT_ORBITS_PER_DAY",
            "ORBIT_WINDOW_COUNT",
            "ORBIT_WINDOW_HORIZON_H",
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
            "TRANSFER_BURNOUT_MASS_KG",
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


#: One probe per knob in ``MISSION_DEFAULTS``: ``key -> (baseline, flipped)``.
#: ``baseline`` is the parameter set the knob is exercised from (empty for all
#: but one knob, which is documented below); ``flipped`` is the value it is
#: moved to. Adding a knob to ``MISSION_DEFAULTS`` without adding a probe here
#: fails ``test_every_knob_has_a_probe`` — that is what makes the enumeration a
#: gate rather than a sample.
KNOB_PROBES: dict[str, tuple[dict[str, object], object]] = {
    "deadline_min": ({}, 30.0),
    "station_altitude_km": ({}, 700.0),
    "launch_horizon_h": ({}, 8.0),
    "crew": ({}, 12),
    "capacity_kg": ({}, 10800.0),
    "rate_kg_per_person_day": ({}, 4.0),
    "resupply_interval_days": ({}, 12.0),
    "park_altitude_km": ({}, 100.0),
    "transfer_isp_s": ({}, 450.0),
    "transfer_dry_mass_kg": ({}, 5000.0),
    "deorbit_perigee_km": ({}, 200.0),
    "rendezvous_intercept_s": ({}, 900.0),
    "centrifuge_target_g": ({}, 4.0),
    "centrifuge_radius_m": ({}, 16.0),
    "centrifuge_sustain_s": ({}, 5.0),
    "ramp_rate_g_per_s": ({}, 1.0),
    "decay_rate_g_per_s": ({}, 2.0),
    # g_limit is the one knob that cannot be exercised from the shipped
    # defaults: the DRAX plateau already fails the *duration* ceiling, so the
    # verdict reads "no" whatever the peak-g ceiling says. Shortening the
    # plateau to 1 s clears the duration ceiling and leaves g_limit as the only
    # thing that can reject the run.
    "g_limit": ({"centrifuge_sustain_s": 1.0}, 5.0),
    "duration_limit_s": ({}, 3.0),
    "centrifuge_margin_fraction": ({}, 0.5),
    "training_daily_cap_g_s": ({}, 50.0),
    "training_weekly_cap_g_s": ({}, 800.0),
    "training_sessions_per_week": ({}, 2),
    "crash_deadline_min": ({}, 55.0),
}


class TestConfigKnobsAreConsumed:
    """Every knob in ``MISSION_DEFAULTS`` must change a result when flipped.

    A parameter that is named but never read is worse than no parameter: it
    advertises control the model does not have. The sweep below is exhaustive
    over ``MISSION_DEFAULTS`` — not a sample of it.
    """

    def test_every_knob_has_a_probe(self) -> None:
        """The probe table must cover ``MISSION_DEFAULTS`` exactly."""
        assert set(KNOB_PROBES) == set(MISSION_DEFAULTS)

    @pytest.mark.parametrize("knob", sorted(MISSION_DEFAULTS))
    def test_knob_moves_a_published_result(self, knob: str) -> None:
        """Flipping this knob must change at least one published token."""
        baseline_overrides, flipped = KNOB_PROBES[knob]
        assert MISSION_DEFAULTS[knob] != flipped, f"{knob}: probe does not change the value"
        base = compute_mission_results(dict(baseline_overrides))
        moved = compute_mission_results({**baseline_overrides, knob: flipped})
        changed = {k for k in base if base[k] != moved[k]}
        assert changed, f"{knob} changed nothing: it is a knob the model does not read"

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


class TestPublishedNumbersAreReDerivable:
    """A reader with only the published tokens must be able to redo the sums."""

    def test_propellant_follows_from_the_published_mass_basis(self) -> None:
        """``propellant = burnout_mass * (mass_ratio - 1)`` — with published values.

        The mass basis is the dry structure *plus* the delivered consumables,
        because the cargo is still aboard through both burns. Publishing
        ``TRANSFER_BURNOUT_MASS_KG`` is what makes the rocket-equation line in
        §Results checkable by hand; without it a reader multiplying the dry mass
        alone lands on a different, smaller number.
        """
        results = compute_mission_results()
        basis = results["TRANSFER_BURNOUT_MASS_KG"]
        assert basis == pytest.approx(
            MISSION_DEFAULTS["transfer_dry_mass_kg"] + MISSION_DEFAULTS["capacity_kg"]
        )
        # Done with the *published*, rounded values — the reader has no others.
        by_hand = basis * (results["TRANSFER_MASS_RATIO"] - 1.0)
        assert by_hand == pytest.approx(results["TRANSFER_PROPELLANT_KG"], abs=0.05)

    def test_window_count_is_bounded_by_the_horizon_not_requested(self) -> None:
        """``ORBIT_WINDOW_COUNT`` must be a filter result, not an echoed input.

        No parameter names the count. Raising the station shortens nothing but
        lengthens its period, so fewer plane crossings fit the same horizon; and
        a horizon shorter than a single pass admits none at all.
        """
        base = compute_mission_results()["ORBIT_WINDOW_COUNT"]
        higher = compute_mission_results({"station_altitude_km": 700.0})["ORBIT_WINDOW_COUNT"]
        longer = compute_mission_results({"launch_horizon_h": 8.0})["ORBIT_WINDOW_COUNT"]
        tiny = compute_mission_results({"launch_horizon_h": 0.05})["ORBIT_WINDOW_COUNT"]
        assert higher < base < longer
        assert tiny == 0

    def test_critical_paths_are_paths_and_the_activity_set_is_not(self) -> None:
        """The published path count and the published activity set differ on purpose."""
        results = compute_mission_results()
        assert results["SHUTTLE_CRITICAL_PATH_COUNT"] == 2
        activities = results["SHUTTLE_CRITICAL_ACTIVITIES"].split(", ")
        paths = results["SHUTTLE_CRITICAL_PATHS"].split("; ")
        assert len(paths) == results["SHUTTLE_CRITICAL_PATH_COUNT"]
        # The set is the union of the paths, and is longer than either of them.
        assert set(activities) == {name for path in paths for name in path.split(" → ")}
        assert all(len(path.split(" → ")) < len(activities) for path in paths)
