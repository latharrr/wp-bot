from datetime import datetime, timezone

from app.core.supabase_client import get_supabase


class SupabaseKeywordRepository:
    def __init__(self) -> None:
        self._client = get_supabase()

    def store_message(self, payload: dict) -> None:
        self._client.table("messages").upsert(payload, on_conflict="message_id").execute()

    def record_watch(self, keyword: str) -> None:
        existing = (
            self._client.table("keyword_watch").select("id,search_count").eq("keyword", keyword).limit(1).execute()
        )
        now = datetime.now(timezone.utc).isoformat()
        if existing.data:
            row = existing.data[0]
            self._client.table("keyword_watch").update(
                {"search_count": row["search_count"] + 1, "last_searched_at": now}
            ).eq("id", row["id"]).execute()
        else:
            self._client.table("keyword_watch").insert({"keyword": keyword, "last_searched_at": now}).execute()

    def list_recent_watches(self, limit: int = 20) -> list[dict]:
        response = (
            self._client.table("keyword_watch")
            .select("*")
            .order("last_searched_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def upsert_match(self, payload: dict) -> None:
        self._client.table("keyword_match").upsert(payload, on_conflict="message_id,keyword").execute()

    def search_messages_ilike(self, keyword: str, limit: int = 500) -> list[dict]:
        """Retroactive search over the full message store -- used to backfill keyword_match
        for terms searched after the fact, not to serve exports directly (those read the
        exportable_keyword_matches view instead, see migration 016)."""
        response = (
            self._client.table("messages")
            .select("*")
            .ilike("message_text", f"%{keyword}%")
            .order("sent_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def list_exportable_matches(self, keyword: str) -> list[dict]:
        response = (
            self._client.table("exportable_keyword_matches")
            .select("*")
            .ilike("keyword", keyword)
            .order("message_date", desc=True)
            .execute()
        )
        return response.data or []

    def count_all_matches(self, keyword: str) -> int:
        response = (
            self._client.table("keyword_match")
            .select("id", count="exact")
            .ilike("keyword", keyword)
            .execute()
        )
        return response.count or 0
