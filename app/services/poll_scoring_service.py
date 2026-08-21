"""Batch CSV propensity scoring, ported from the reference repo's poll_scoring_service.py."""
import io

import pandas as pd

from app.repositories.supabase_poll_repository import SupabasePollRepository
from app.services.csv_parser import parse_poll_csv
from app.services.scoring import calculate_prediction_score

DEFAULT_THRESHOLD = 70.0


class PollScoringService:
    def __init__(self) -> None:
        self._polls = SupabasePollRepository()

    def score_csv(self, raw_bytes: bytes, source_filename: str, threshold: float = DEFAULT_THRESHOLD) -> dict:
        df = parse_poll_csv(raw_bytes)

        mobiles = df["mobile"].unique().tolist()
        history_rows = self._polls.fetch_user_history(mobiles)
        history_by_mobile = {row["mobile"]: row for row in history_rows}

        scores = []
        for _, row in df.iterrows():
            history = history_by_mobile.get(row["mobile"], {})
            score = calculate_prediction_score(history, row["poll_date"])
            scores.append(score)
        df["prediction_score"] = scores

        prediction_rows = [
            {
                "mobile": row["mobile"],
                "product_name": row.get("product_name"),
                "poll_date": row["poll_date"].isoformat(),
                "vote": row["vote"],
                "prediction_score": row["prediction_score"],
                "source_filename": source_filename,
            }
            for _, row in df.iterrows()
        ]
        self._polls.upsert_predictions(prediction_rows)

        above_threshold_count = int((df["prediction_score"] >= threshold).sum())

        output = io.StringIO()
        df.to_csv(output, index=False)

        return {
            "scored_csv": output.getvalue(),
            "above_threshold_count": above_threshold_count,
            "row_count": len(df),
        }


def get_poll_scoring_service() -> PollScoringService:
    return PollScoringService()
