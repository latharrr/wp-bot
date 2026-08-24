
from app.core.supabase_client import get_supabase


class SupabaseAdminRepository:
    def __init__(self) -> None:
        self._client = get_supabase()

    def get_by_username(self, username: str) -> dict | None:
        response = (
            self._client.table("admin_users").select("*").eq("username", username).limit(1).execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def create(
        self, username: str, password_hash: str, role: str = "user", allowed_features: list[str] | None = None
    ) -> None:
        self._client.table("admin_users").insert(
            {
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "allowed_features": allowed_features or [],
            }
        ).execute()

    def list_users(self) -> list[dict]:
        response = (
            self._client.table("admin_users")
            .select("username,role,allowed_features,created_at")
            .order("created_at")
            .execute()
        )
        return response.data or []

    def update_features(self, username: str, allowed_features: list[str]) -> None:
        self._client.table("admin_users").update({"allowed_features": allowed_features}).eq(
            "username", username
        ).execute()

    def delete_user(self, username: str) -> None:
        self._client.table("admin_users").delete().eq("username", username).execute()
