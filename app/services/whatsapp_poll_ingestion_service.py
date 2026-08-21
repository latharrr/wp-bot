from datetime import datetime, timezone

from app.models.whatsapp import PollCreatedPayload, PollVotePayload
from app.repositories.supabase_poll_repository import SupabasePollRepository


class WhatsappPollIngestionService:
    def __init__(self) -> None:
        self._polls = SupabasePollRepository()

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

        vote_timestamp = datetime.fromtimestamp(payload.vote_timestamp_ms / 1000, tz=timezone.utc).isoformat()

        self._polls.insert_vote_event_if_new(
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
                "vote_timestamp": vote_timestamp,
            },
        )

        self._polls.upsert_vote_snapshot(
            {
                "group_jid": payload.group_jid,
                "poll_message_id": payload.poll_message_id,
                "poll_title": payload.poll_title,
                "voter_jid": payload.voter_jid,
                "voter_phone": payload.voter_phone,
                "voter_name": payload.voter_name,
                "selected_options": payload.selected_options,
                "last_vote_timestamp": vote_timestamp,
            }
        )


def get_poll_ingestion_service() -> WhatsappPollIngestionService:
    return WhatsappPollIngestionService()
