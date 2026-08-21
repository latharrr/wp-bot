from typing import Optional

from app.core.supabase_client import get_supabase


class SupabaseAdminRepository:
    def __init__(self) -> None:
        self._client = get_supabase()

    def get_by_username(self, username: str) -> Optional[dict]:
        response = (
            self._client.table("admin_users").select("*").eq("username", username).limit(1).execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def create(self, username: str, password_hash: str) -> None:
        self._client.table("admin_users").insert({"username": username, "password_hash": password_hash}).execute()
