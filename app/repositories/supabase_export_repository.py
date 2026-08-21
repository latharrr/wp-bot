from app.core.supabase_client import get_supabase
from app.models.export import ExportAuditLogEntry


class SupabaseExportRepository:
    def __init__(self) -> None:
        self._client = get_supabase()

    def log_export(self, entry: ExportAuditLogEntry) -> None:
        self._client.table("export_audit_log").insert(entry.to_supabase_payload()).execute()

    def list_recent(self, limit: int = 100) -> list[dict]:
        response = (
            self._client.table("export_audit_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
