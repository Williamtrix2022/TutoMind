import random
from datetime import UTC, datetime, timedelta

import pytest

from app.services.risk import (
    GREEN_BELOW,
    RED_FROM,
    WEIGHTS,
    Grade,
    StudentActivity,
    compute_risk,
    level_for,
    summarize,
)

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


def activity(**overrides) -> StudentActivity:
    base = {
        "student_id": "s1",
        "name": "Ana Torres",
        "last_activity_at": NOW - timedelta(hours=5),
        "grades": [],
        "missed_deadlines": 0,
        "submissions": 0,
        "questions": 0,
        "scored_messages": 0,
        "frustrated_messages": 0,
        "open_tickets": 0,
    }
    return StudentActivity(**{**base, **overrides})


def factors_by_key(risk):
    return {f.key: f for f in risk.factors}


class TestLevels:
    @pytest.mark.parametrize(
        ("score", "level"),
        [(0.0, "green"), (0.399, "green"), (GREEN_BELOW, "yellow"), (0.649, "yellow"),
         (RED_FROM, "red"), (1.0, "red")],
    )  # fmt: skip
    def test_thresholds(self, score, level):
        assert level_for(score) == level

    def test_weights_add_up_to_one(self):
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)


class TestProfiles:
    def test_engaged_student_with_good_grades_is_green(self):
        risk = compute_risk(
            activity(grades=[Grade(4.5, 5), Grade(4.2, 5)], submissions=3, questions=6), NOW
        )

        assert risk.risk_level == "green"
        assert risk.risk_score < GREEN_BELOW
        assert risk.projected_grade >= 4.0

    def test_absent_student_with_bad_grades_and_missed_work_is_red(self):
        risk = compute_risk(
            activity(
                last_activity_at=NOW - timedelta(days=12),
                grades=[Grade(2.0, 5), Grade(1.8, 5)],
                missed_deadlines=3,
                scored_messages=3,
                frustrated_messages=2,
                open_tickets=1,
            ),
            NOW,
        )

        assert risk.risk_level == "red"
        assert risk.projected_grade < 2.5

    def test_a_student_with_no_recorded_activity_is_flagged(self):
        risk = compute_risk(activity(last_activity_at=None), NOW)

        login = factors_by_key(risk)["days_since_last_login"]
        assert login.value == "Sin actividad registrada"
        assert login.impact > 0
        assert risk.risk_level == "red"

    def test_middle_of_the_road_student_is_yellow(self):
        risk = compute_risk(
            activity(
                last_activity_at=NOW - timedelta(days=5),
                grades=[Grade(3.2, 5)],
                missed_deadlines=1,
                questions=1,
            ),
            NOW,
        )

        assert risk.risk_level == "yellow"


class TestFactors:
    def test_inactivity_explains_itself_in_days(self):
        risk = compute_risk(activity(last_activity_at=NOW - timedelta(days=12, hours=3)), NOW)

        login = factors_by_key(risk)["days_since_last_login"]
        assert login.value == 12
        assert "12 días" in login.explanation
        assert login.impact > 0

    def test_logging_in_today_lowers_the_risk(self):
        login = factors_by_key(compute_risk(activity(), NOW))["days_since_last_login"]

        assert login.impact < 0 and "hoy" in login.explanation

    def test_grades_are_compared_on_a_common_scale(self):
        five = compute_risk(activity(grades=[Grade(4.0, 5)]), NOW)
        ten = compute_risk(activity(grades=[Grade(8.0, 10)]), NOW)

        assert (
            factors_by_key(five)["average_grade"].impact
            == factors_by_key(ten)["average_grade"].impact
        )

    def test_without_grades_there_is_no_grade_factor(self):
        assert "average_grade" not in factors_by_key(compute_risk(activity(), NOW))

    def test_missed_deadlines_raise_risk_and_on_time_work_lowers_it(self):
        missed = factors_by_key(compute_risk(activity(missed_deadlines=3), NOW))
        on_time = factors_by_key(compute_risk(activity(submissions=4), NOW))

        assert missed["missed_assignments"].impact > 0
        assert on_time["missed_assignments"].impact < 0

    def test_no_work_registered_means_no_assignment_factor(self):
        assert "missed_assignments" not in factors_by_key(compute_risk(activity(), NOW))

    def test_frustration_factor_needs_scored_messages(self):
        none = factors_by_key(compute_risk(activity(), NOW))
        some = factors_by_key(compute_risk(activity(scored_messages=4, frustrated_messages=3), NOW))

        assert "tutor_confusion" not in none
        assert some["tutor_confusion"].impact > 0
        assert some["tutor_confusion"].value == "3 de 4 mensajes"

    def test_calm_conversations_count_in_favour(self):
        calm = factors_by_key(compute_risk(activity(scored_messages=4), NOW))

        assert calm["tutor_confusion"].impact < 0

    def test_open_tickets_only_appear_when_there_are_some(self):
        assert "open_tickets" not in factors_by_key(compute_risk(activity(), NOW))
        assert (
            factors_by_key(compute_risk(activity(open_tickets=2), NOW))["open_tickets"].impact > 0
        )

    def test_not_using_the_tutor_counts_against_and_using_it_counts_in_favour(self):
        idle = factors_by_key(compute_risk(activity(questions=0), NOW))["tutor_usage"]
        busy = factors_by_key(compute_risk(activity(questions=5), NOW))["tutor_usage"]

        assert idle.impact > 0 > busy.impact

    def test_factors_are_ordered_by_how_much_they_weigh(self):
        risk = compute_risk(
            activity(last_activity_at=NOW - timedelta(days=20), grades=[Grade(1, 5)]), NOW
        )

        impacts = [abs(f.impact) for f in risk.factors]
        assert impacts == sorted(impacts, reverse=True)

    def test_explanations_are_natural_language_in_spanish(self):
        risk = compute_risk(activity(grades=[Grade(2.0, 5)], missed_deadlines=2), NOW)

        assert all(f.explanation.endswith(".") and len(f.explanation) > 10 for f in risk.factors)


class TestProjectedGrade:
    def test_with_grades_it_starts_from_the_average(self):
        risk = compute_risk(activity(grades=[Grade(4.0, 5)], questions=4), NOW)

        assert 3.5 <= risk.projected_grade <= 5.0

    def test_other_risk_factors_pull_it_down(self):
        calm = compute_risk(activity(grades=[Grade(4.0, 5)], questions=4), NOW)
        troubled = compute_risk(
            activity(
                grades=[Grade(4.0, 5)],
                last_activity_at=NOW - timedelta(days=15),
                missed_deadlines=3,
            ),
            NOW,
        )

        assert troubled.projected_grade < calm.projected_grade

    def test_without_grades_a_neutral_base_is_used(self):
        risk = compute_risk(activity(questions=2), NOW)

        assert 2.5 <= risk.projected_grade <= 3.5

    def test_scale_is_reported(self):
        assert compute_risk(activity(), NOW).grade_scale_max == 5


class TestInvariants:
    """What the dashboard promises the teacher, whatever the data looks like."""

    @staticmethod
    def random_activity(rng: random.Random) -> StudentActivity:
        scored = rng.randint(0, 8)
        return activity(
            last_activity_at=rng.choice([None, NOW - timedelta(days=rng.uniform(0, 40))]),
            grades=[Grade(rng.uniform(0, 10), 10) for _ in range(rng.randint(0, 5))],
            missed_deadlines=rng.randint(0, 6),
            submissions=rng.randint(0, 6),
            questions=rng.randint(0, 12),
            scored_messages=scored,
            frustrated_messages=rng.randint(0, scored),
            open_tickets=rng.randint(0, 3),
        )

    def test_every_risk_is_well_formed_and_explainable(self):
        rng = random.Random(7)
        for _ in range(300):
            risk = compute_risk(self.random_activity(rng), NOW)

            assert risk.factors, "every risk level must ship with explicit XAI factors"
            assert all(-1 <= f.impact <= 1 for f in risk.factors)
            assert 0 <= risk.risk_score <= 1
            assert 0 <= risk.projected_grade <= risk.grade_scale_max
            assert risk.risk_level == level_for(risk.risk_score)
            # The score is the neutral 0.5 plus what each factor contributes.
            explained = min(1.0, max(0.0, 0.5 + sum(f.impact for f in risk.factors)))
            assert risk.risk_score == pytest.approx(explained, abs=1e-3)

    def test_more_days_without_activity_never_lowers_the_risk(self):
        scores = [
            compute_risk(activity(last_activity_at=NOW - timedelta(days=d)), NOW).risk_score
            for d in range(0, 30)
        ]

        assert scores == sorted(scores)

    def test_more_missed_deadlines_never_lowers_the_risk(self):
        scores = [compute_risk(activity(missed_deadlines=m, submissions=2), NOW).risk_score
                  for m in range(0, 6)]  # fmt: skip

        assert scores == sorted(scores)

    def test_better_grades_never_raise_the_risk(self):
        scores = [compute_risk(activity(grades=[Grade(g, 5)]), NOW).risk_score
                  for g in (0, 1, 2, 3, 4, 5)]  # fmt: skip

        assert scores == sorted(scores, reverse=True)

    def test_updated_at_is_the_computation_time(self):
        assert compute_risk(activity(), NOW).updated_at == NOW


class TestSummary:
    def test_counts_each_level(self):
        good = compute_risk(activity(grades=[Grade(5, 5)], questions=6, submissions=2), NOW)
        bad = compute_risk(activity(last_activity_at=None), NOW)

        summary = summarize([good, bad, bad])

        assert (summary.green, summary.yellow, summary.red) == (1, 0, 2)

    def test_empty_course(self):
        summary = summarize([])

        assert (summary.green, summary.yellow, summary.red) == (0, 0, 0)
