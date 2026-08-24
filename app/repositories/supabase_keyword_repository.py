from datetime import UTC, datetime

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
        now = datetime.now(UTC).isoformat()
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

    def list_all_keywords(self) -> list[dict]:
        """The full managed watchlist (Keywords admin page) -- distinct from
        list_recent_watches, which is bounded/ordered for the "recent searches" shortcut list."""
        response = self._client.table("keyword_watch").select("*").order("keyword").execute()
        return response.data or []

    def add_keywords(self, keywords: list[str]) -> list[dict]:
        """Explicitly register keywords for continuous matching -- unlike record_watch (called
        implicitly by an ad-hoc search), this is the operator saying "watch for this" without
        needing to search for it first. Idempotent: already-registered keywords are left alone
        (in particular, their is_active/search_count aren't reset)."""
        existing = {row["keyword"] for row in self.list_all_keywords()}
        results = []
        now = datetime.now(UTC).isoformat()
        for keyword in dict.fromkeys(k.strip().lower() for k in keywords if k.strip()):
            already_existed = keyword in existing
            if not already_existed:
                self._client.table("keyword_watch").insert(
                    {"keyword": keyword, "search_count": 0, "last_searched_at": now}
                ).execute()
            results.append({"keyword": keyword, "added": not already_existed, "already_existed": already_existed})
        return results

    def set_keywords_enabled(self, keywords: list[str], enabled: bool) -> list[dict]:
        existing = {row["keyword"]: row["id"] for row in self.list_all_keywords()}
        results = []
        for keyword in dict.fromkeys(k.strip().lower() for k in keywords if k.strip()):
            row_id = existing.get(keyword)
            if row_id:
                self._client.table("keyword_watch").update({"is_active": enabled}).eq("id", row_id).execute()
            results.append({"keyword": keyword, "enabled": enabled, "found": row_id is not None})
        return results

    def delete_keywords(self, keywords: list[str]) -> list[dict]:
        existing = {row["keyword"] for row in self.list_all_keywords()}
        results = []
        for keyword in dict.fromkeys(k.strip().lower() for k in keywords if k.strip()):
            found = keyword in existing
            if found:
                self._client.table("keyword_watch").delete().eq("keyword", keyword).execute()
            results.append({"keyword": keyword, "deleted": found})
        return results

    def upsert_match(self, payload: dict) -> None:
        self._client.table("keyword_match").upsert(payload, on_conflict="message_id,keyword").execute()

    def search_messages_ilike(self, keyword: str, limit: int = 500) -> list[dict]:
        """Retroactive search over the full message store -- used to backfill keyword_match
        for terms searched after the fact, not to serve results directly (see
        list_matches_in_consented_groups for that)."""
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
        """The strict double-gate (group consent AND individual opt-in) -- kept for anything
        that still needs it, but keyword search itself now uses
        list_matches_in_consented_groups (see that method's docstring for why)."""
        response = (
            self._client.table("exportable_keyword_matches")
            .select("*")
            .ilike("keyword", keyword)
            .order("message_date", desc=True)
            .execute()
        )
        return response.data or []

    def list_matches_in_consented_groups(self, keyword: str, consented_group_jids: list[str]) -> list[dict]:
        """Group-consent-only gate for keyword matches, deliberately chosen to match the same
        precedent poll voter breakdowns already use ("this content is already visible to
        everyone in the group natively; the group's own consent is what authorizes recording/
        monitoring it, not each member's individual opt-in"). Contacts remains the stricter
        double-gate since building an external outreach list is a materially different action
        than viewing conversation content."""
        if not consented_group_jids:
            return []
        response = (
            self._client.table("keyword_match")
            .select("keyword,group_jid,sender_jid,sender_name,sender_phone,message,message_id,message_date")
            .ilike("keyword", keyword)
            .in_("group_jid", consented_group_jids)
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

    def list_messages_for_group(self, group_jid: str, page: int, page_size: int) -> tuple[list[dict], int]:
        """Backing the group Messages monitor -- only called once the caller has already
        confirmed the group is consented (same pattern as poll voter breakdowns)."""
        start = (page - 1) * page_size
        response = (
            self._client.table("messages")
            .select("sender_jid,sender_phone,sender_name,message_text,sent_at", count="exact")
            .eq("group_jid", group_jid)
            .order("sent_at", desc=True)
            .range(start, start + page_size - 1)
            .execute()
        )
        return response.data or [], response.count or 0

    def count_messages_for_group(self, group_jid: str) -> int:
        response = self._client.table("messages").select("id", count="exact").eq("group_jid", group_jid).execute()
        return response.count or 0
