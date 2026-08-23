from datetime import datetime, timezone
from typing import Optional

from app.core.supabase_client import get_supabase
from app.models.consent import ConsentPromptRecord, MemberConsentRecord


class SupabaseConsentRepository:
    def __init__(self) -> None:
        self._client = get_supabase()

    def deactivate_active_prompts(self, group_jid: str) -> None:
        self._client.table("consent_prompts").update({"is_active": False}).eq(
            "group_jid", group_jid
        ).eq("is_active", True).execute()

    def create_prompt(self, prompt: ConsentPromptRecord) -> None:
        self.deactivate_active_prompts(prompt.group_jid)
        self._client.table("consent_prompts").insert(prompt.to_supabase_payload()).execute()

    def get_active_prompt_by_message_id(self, message_id: str) -> Optional[dict]:
        response = (
            self._client.table("consent_prompts")
            .select("*")
            .eq("message_id", message_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def record_opt_in(self, record: MemberConsentRecord) -> None:
        self.bulk_record_opt_in([record])

    def bulk_record_opt_in(self, records: list[MemberConsentRecord]) -> None:
        if not records:
            return
        rows = []
        for record in records:
            payload = record.to_supabase_payload()
            payload["opted_out_at"] = None
            rows.append(payload)
        self._client.table("member_consent").upsert(rows, on_conflict="group_jid,member_phone").execute()

    def record_opt_out(self, group_jid: str, member_phone: str) -> None:
        self._client.table("member_consent").update(
            {"opted_in": False, "opted_out_at": datetime.now(timezone.utc).isoformat()}
        ).eq("group_jid", group_jid).eq("member_phone", member_phone).execute()

    def list_member_consent(self, group_jid: str) -> list[dict]:
        response = (
            self._client.table("member_consent").select("*").eq("group_jid", group_jid).execute()
        )
        return response.data or []
