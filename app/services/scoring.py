"""Ported verbatim (logic-wise) from the reference repo's app/services/scoring.py."""
from datetime import date
from typing import Optional


def _days_since(reference_date: date, past_date: Optional[date]) -> Optional[int]:
    if past_date is None:
        return None
    return (reference_date - past_date).days


def calculate_prediction_score(history: dict, poll_date: date) -> float:
    total_purchases = history.get("total_purchases") or 0
    last_purchase_date = history.get("last_purchase_date")
    purchases_last_30_days = history.get("purchases_last_30_days") or 0
    purchases_last_60_days = history.get("purchases_last_60_days") or 0
    total_yes_votes = history.get("total_yes_votes") or 0
    last_vote_converted = history.get("last_vote_converted")
    n_2_vote_converted = history.get("n_2_vote_converted")

    days_since_purchase = _days_since(poll_date, last_purchase_date)

    if total_yes_votes <= 0:
        score = 50.0
        if days_since_purchase is not None:
            if days_since_purchase < 15:
                score += 20
            elif days_since_purchase < 30:
                score += 15
            else:
                score += 10
    else:
        score = 20.0

        if purchases_last_30_days >= 3:
            score += 20
        if purchases_last_60_days >= 5:
            score += 10

        if days_since_purchase is not None:
            if days_since_purchase < 15:
                score += 15
            elif days_since_purchase < 30:
                score += 10

        if last_vote_converted is True:
            score += 20
        elif last_vote_converted is False:
            score -= 5

        if n_2_vote_converted is True:
            score += 15
        elif n_2_vote_converted is False:
            score -= 5

        if total_yes_votes > 0:
            score += min((total_purchases / total_yes_votes) * 10, 10)

    return round(max(0.0, min(100.0, score)), 2)
