from datetime import UTC, datetime

from app.core.supabase_client import get_supabase

KEYWORD_ANALYSIS = "keyword_analysis"
PROPENSITY_SCORING = "propensity_scoring"


class SupabaseFeatureToggleRepository:
    def __init__(self) -> None:
        self._client = get_supabase()

    def is_enabled(self, key: str, default: bool = True) -> bool:
        response = self._client.table("feature_toggles").select("enabled").eq("key", key).limit(1).execute()
        rows = response.data or []
        return bool(rows[0]["enabled"]) if rows else default

    def set_enabled(self, key: str, enabled: bool) -> None:
        self._client.table("feature_toggles").upsert(
            {"key": key, "enabled": enabled, "updated_at": datetime.now(UTC).isoformat()},
            on_conflict="key",
        ).execute()

    def list_all(self) -> list[dict]:
        response = self._client.table("feature_toggles").select("*").order("key").execute()
        return response.data or []
