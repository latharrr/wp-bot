from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.supabase_client import get_supabase


class SupabasePollRepository:
    def __init__(self) -> None:
        self._client = get_supabase()
        self._settings = get_settings()

    # --- live ingestion ---

    def upsert_poll(
        self,
        group_jid: str,
        group_name: str | None,
        poll_message_id: str,
        poll_title: str,
        poll_options: list[str],
        poll_created_at_ms: int,
    ) -> None:
        payload = {
            "group_jid": group_jid,
            "group_name": group_name,
            "poll_message_id": poll_message_id,
            "poll_title": poll_title,
            "poll_options": poll_options,
            "poll_created_at": datetime.fromtimestamp(poll_created_at_ms / 1000, tz=UTC).isoformat(),
        }
        self._client.table("whatsapp_poll").upsert(payload, on_conflict="poll_message_id").execute()

    def insert_vote_event_if_new(self, dedupe_key: str, payload: dict) -> bool:
        existing = (
            self._client.table("whatsapp_poll_vote_event")
            .select("id")
            .eq("dedupe_key", dedupe_key)
            .limit(1)
            .execute()
        )
        if existing.data:
            return False
        self._client.table("whatsapp_poll_vote_event").insert(payload).execute()
        return True

    def upsert_vote_snapshot(self, payload: dict) -> None:
        self._client.table("whatsapp_poll_vote_snapshot").upsert(
            payload, on_conflict="poll_message_id,voter_jid"
        ).execute()

    # --- dashboard reads ---

    def list_polls_for_group(self, group_jid: str) -> list[dict]:
        response = (
            self._client.table("whatsapp_poll")
            .select("*")
            .eq("group_jid", group_jid)
            .order("poll_created_at", desc=True)
            .execute()
        )
        return response.data or []

    def get_poll(self, poll_message_id: str) -> dict | None:
        response = (
            self._client.table("whatsapp_poll")
            .select("*")
            .eq("poll_message_id", poll_message_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def get_voter_breakdown(self, poll_message_id: str) -> list[dict]:
        """Full, named breakdown -- only call when the poll's group is consent_status='consented'."""
        response = (
            self._client.table("whatsapp_poll_vote_snapshot")
            .select("voter_jid,voter_phone,voter_name,selected_options,last_vote_timestamp")
            .eq("poll_message_id", poll_message_id)
            .execute()
        )
        return response.data or []

    def get_vote_aggregate(self, poll_message_id: str) -> dict:
        """Counts-only query for non-consented groups -- never selects voter_jid/voter_phone."""
        response = (
            self._client.table("whatsapp_poll_vote_snapshot")
            .select("selected_options")
            .eq("poll_message_id", poll_message_id)
            .execute()
        )
        counts: dict[str, int] = {}
        for row in response.data or []:
            for option in row.get("selected_options") or []:
                counts[option] = counts.get(option, 0) + 1
        return counts

    # --- CSV batch scoring (ported from the reference repo) ---

    def fetch_user_history(self, mobiles: list[str]) -> list[dict]:
        response = self._client.rpc(self._settings.supabase_poll_history_rpc, {"mobiles": mobiles}).execute()
        return response.data or []

    def upsert_predictions(self, rows: list[dict]) -> None:
        if not rows:
            return
        self._client.table("poll_prediction").upsert(rows, on_conflict="mobile,source_filename").execute()
