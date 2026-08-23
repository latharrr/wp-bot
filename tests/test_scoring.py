from datetime import date

from app.services.scoring import calculate_prediction_score


def test_no_prior_yes_votes_uses_base_50_and_recent_purchase_bonus():
    history = {
        "total_purchases": 2,
        "last_purchase_date": date(2026, 8, 10),
        "total_yes_votes": 0,
    }
    score = calculate_prediction_score(history, date(2026, 8, 20))
    assert score == 70.0


def test_no_prior_yes_votes_no_purchase_history_stays_at_base():
    history = {"total_yes_votes": 0}
    score = calculate_prediction_score(history, date(2026, 8, 20))
    assert score == 50.0


def test_no_prior_yes_votes_old_purchase_gets_smallest_bonus():
    history = {
        "last_purchase_date": date(2026, 6, 1),
        "total_yes_votes": 0,
    }
    score = calculate_prediction_score(history, date(2026, 8, 20))
    assert score == 60.0


def test_engaged_voter_with_strong_signals_scores_high():
    history = {
        "total_purchases": 6,
        "last_purchase_date": date(2026, 8, 15),
        "purchases_last_30_days": 3,
        "purchases_last_60_days": 5,
        "total_yes_votes": 4,
        "last_vote_converted": True,
        "n_2_vote_converted": True,
    }
    score = calculate_prediction_score(history, date(2026, 8, 20))
    # 20 base + 20 (30d) + 10 (60d) + 15 (days<15) + 20 (last converted) + 15 (n-2 converted)
    # + min((6/4)*10, 10) = 10 -> 110, clamped to 100
    assert score == 100.0


def test_engaged_voter_with_negative_signals_scores_low():
    history = {
        "total_purchases": 0,
        "total_yes_votes": 2,
        "last_vote_converted": False,
        "n_2_vote_converted": False,
    }
    score = calculate_prediction_score(history, date(2026, 8, 20))
    # 20 base - 5 - 5 = 10
    assert score == 10.0


def test_score_is_clamped_between_0_and_100():
    history = {"total_yes_votes": 2, "last_vote_converted": False, "n_2_vote_converted": False}
    score = calculate_prediction_score(history, date(2026, 8, 20))
    assert 0.0 <= score <= 100.0


def test_missing_history_fields_default_sensibly():
    score = calculate_prediction_score({}, date(2026, 8, 20))
    assert score == 50.0
