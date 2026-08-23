from app.repositories.supabase_keyword_repository import SupabaseKeywordRepository


class KeywordSearchService:
    def __init__(self) -> None:
        self._keywords = SupabaseKeywordRepository()

    def check_message_for_keywords(self, keyword_candidates: list[str], message_row: dict) -> None:
        text_lower = message_row["message_text"].lower()
        for keyword in keyword_candidates:
            if keyword.lower() in text_lower:
                self._keywords.upsert_match(
                    {
                        "keyword": keyword,
                        "group_jid": message_row["group_jid"],
                        "sender_jid": message_row["sender_jid"],
                        "sender_name": message_row.get("sender_name"),
                        "sender_phone": message_row.get("sender_phone"),
                        "message": message_row["message_text"],
                        "message_id": message_row["message_id"],
                        "message_date": message_row["sent_at"],
                    }
                )

    def search(self, keyword: str) -> dict:
        """Retroactively scans the full message store for the term (catches messages sent
        before this keyword was ever searched), backfills keyword_match, records the search
        in keyword_watch, then returns only exportable (consent-gated) hits plus a
        non-identifying count of how many additional hits exist but aren't consented."""
        # Normalize case so "PG" and "pg" are the same keyword_watch entry -- record_watch and
        # upsert_match key on exact string equality, not the ilike used for message matching.
        keyword = keyword.strip().lower()
        if not keyword:
            return {"keyword": keyword, "results": [], "hidden_match_count": 0}

        for message_row in self._keywords.search_messages_ilike(keyword):
            self.check_message_for_keywords([keyword], message_row)

        self._keywords.record_watch(keyword)

        exportable = self._keywords.list_exportable_matches(keyword)
        total = self._keywords.count_all_matches(keyword)
        hidden = max(total - len(exportable), 0)
        return {"keyword": keyword, "results": exportable, "hidden_match_count": hidden}

    def recent_searches(self) -> list[dict]:
        return self._keywords.list_recent_watches()


def get_keyword_search_service() -> KeywordSearchService:
    return KeywordSearchService()
