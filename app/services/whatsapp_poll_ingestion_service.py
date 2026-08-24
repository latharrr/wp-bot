import logging
from datetime import UTC, datetime

from app.models.whatsapp import PollCreatedPayload, PollVotePayload
from app.repositories.supabase_feature_toggle_repository import (
    PROPENSITY_SCORING,
    SupabaseFeatureToggleRepository,
)
from app.repositories.supabase_poll_repository import SupabasePollRepository
from app.services.scoring import calculate_prediction_score
from app.services.vote_normalization import normalize_vote

logger = logging.getLogger(__name__)


class WhatsappPollIngestionService:
    def __init__(self) -> None:
        self._polls = SupabasePollRepository()
        self._toggles = SupabaseFeatureToggleRepository()

    def handle_poll_created(self, payload: PollCreatedPayload) -> None:
        self._polls.upsert_poll(
            group_jid=payload.group_jid,
            group_name=payload.group_name,
            poll_message_id=payload.poll_message_id,
            poll_title=payload.poll_title,
            poll_options=payload.poll_options,
            poll_created_at_ms=payload.poll_created_at_ms,
        )

    def handle_poll_vote(self, payload: PollVotePayload) -> None:
        # Upsert the poll definition defensively -- the vote may arrive before/without a
        # poll-created event being observed (e.g. bridge restarted mid-poll).
        self._polls.upsert_poll(
            group_jid=payload.group_jid,
            group_name=None,
            poll_message_id=payload.poll_message_id,
            poll_title=payload.poll_title,
            poll_options=payload.poll_options,
            poll_created_at_ms=payload.vote_timestamp_ms,
        )

        vote_timestamp_dt = datetime.fromtimestamp(payload.vote_timestamp_ms / 1000, tz=UTC)
        vote_timestamp = vote_timestamp_dt.isoformat()
        normalized = normalize_vote(payload.poll_options, payload.selected_options)

        inserted = self._polls.insert_vote_event_if_new(
            payload.dedupe_key,
            {
                "dedupe_key": payload.dedupe_key,
                "group_jid": payload.group_jid,
                "poll_message_id": payload.poll_message_id,
                "poll_title": payload.poll_title,
                "voter_jid": payload.voter_jid,
                "voter_phone": payload.voter_phone,
                "voter_name": payload.voter_name,
                "selected_options": payload.selected_options,
                "normalized_vote": normalized,
                "vote_timestamp": vote_timestamp,
            },
        )
        if not inserted:
            logger.info("Skipping duplicate poll vote dedupe_key=%s", payload.dedupe_key)
            return

        self._polls.upsert_vote_snapshot(
            {
                "group_jid": payload.group_jid,
                "poll_message_id": payload.poll_message_id,
                "poll_title": payload.poll_title,
                "voter_jid": payload.voter_jid,
                "voter_phone": payload.voter_phone,
                "voter_name": payload.voter_name,
                "selected_options": payload.selected_options,
                "normalized_vote": normalized,
                "last_vote_timestamp": vote_timestamp,
            }
        )

        self._maybe_score_live_vote(payload, normalized, vote_timestamp_dt)

    def _maybe_score_live_vote(self, payload: PollVotePayload, normalized: int | None, vote_timestamp: datetime) -> None:
        """Ported from poison-br09/whatsapp-propensity-scoring: a live vote on a recognizable
        binary yes/no poll gets scored the instant it arrives, the same way a CSV row would be --
        no manual export/upload needed. Only fires for the "yes" side, matching the reference
        behavior (a "no" has no meaningful propensity to project)."""
        if not payload.voter_phone or normalized is None:
            return
        if not self._toggles.is_enabled(PROPENSITY_SCORING):
            return
        if normalized != 1:
            return

        history_rows = self._polls.fetch_user_history([payload.voter_phone])
        history = next((row for row in history_rows if row.get("mobile") == payload.voter_phone), {})
        score = calculate_prediction_score(history, vote_timestamp.date())

        self._polls.upsert_predictions(
            [
                {
                    "mobile": payload.voter_phone,
                    "product_name": payload.poll_title or "WhatsApp Poll",
                    "poll_date": vote_timestamp.date().isoformat(),
                    "vote": "yes",
                    "prediction_score": score,
                    "source_filename": f"whatsapp:{payload.poll_message_id}",
                }
            ]
        )
        logger.info(
            "Live-scored poll vote mobile=%s poll_message_id=%s score=%s",
            payload.voter_phone,
            payload.poll_message_id,
            score,
        )


def get_poll_ingestion_service() -> WhatsappPollIngestionService:
    return WhatsappPollIngestionService()
