from datetime import UTC, datetime

from app.core.supabase_client import get_supabase
from app.models.group import GroupMemberRecord


class SupabaseGroupRepository:
    def __init__(self) -> None:
        self._client = get_supabase()

    def upsert_group(self, group_jid: str, group_name: str | None, member_count: int) -> None:
        payload = {
            "group_jid": group_jid,
            "group_name": group_name,
            "member_count": member_count,
            "last_synced_at": datetime.now(UTC).isoformat(),
        }
        self._client.table("groups").upsert(payload, on_conflict="group_jid").execute()

    def upsert_members(self, group_jid: str, members: list[GroupMemberRecord]) -> None:
        if not members:
            return
        now = datetime.now(UTC).isoformat()
        rows = []
        for member in members:
            row = member.to_supabase_payload()
            row["last_seen_at"] = now
            rows.append(row)
        self._client.table("group_members").upsert(rows, on_conflict="group_jid,member_jid").execute()

    def list_groups(self) -> list[dict]:
        response = (
            self._client.table("groups")
            .select("*")
            .order("group_name")
            .execute()
        )
        return response.data or []

    def get_group(self, group_jid: str) -> dict | None:
        response = (
            self._client.table("groups").select("*").eq("group_jid", group_jid).limit(1).execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def list_members(self, group_jid: str) -> list[dict]:
        response = (
            self._client.table("group_members")
            .select("*")
            .eq("group_jid", group_jid)
            .order("display_name")
            .execute()
        )
        return response.data or []

    def list_consented_groups(self) -> list[dict]:
        response = (
            self._client.table("groups").select("group_jid,group_name").eq("consent_status", "consented").execute()
        )
        return response.data or []

    def get_member_phone(self, group_jid: str, member_jid: str) -> str | None:
        """The authoritative phone for a member identity, resolved once via groupMetadata's
        phoneNumber field (see whatsapp_bridge/src/handlers/groups.ts) and stored here. Message
        and reaction events should look up phone this way rather than trusting their own
        per-event fields, which Baileys doesn't reliably populate for @lid-addressed groups --
        otherwise the same person ends up with two different "phone" values across tables and
        consent (keyed on phone) silently stops matching.
        """
        response = (
            self._client.table("group_members")
            .select("phone")
            .eq("group_jid", group_jid)
            .eq("member_jid", member_jid)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0]["phone"] if rows else None

    def list_exportable_contacts(self, group_jid: str) -> list[dict]:
        """Reads ONLY from the exportable_contacts view -- see migration 016. Never query
        group_members directly for anything that leaves the process as an export or a
        person-identifying dashboard view."""
        response = (
            self._client.table("exportable_contacts")
            .select("*")
            .eq("group_jid", group_jid)
            .execute()
        )
        return response.data or []

    def set_consent_status(self, group_jid: str, status: str, actor: str) -> None:
        now = datetime.now(UTC).isoformat()
        self._client.table("groups").update(
            {"consent_status": status, "consent_marked_by": actor, "consent_marked_at": now}
        ).eq("group_jid", group_jid).execute()
        action = "consented" if status == "consented" else "revoked"
        self._client.table("group_consent_log").insert(
            {"group_jid": group_jid, "action": action, "actor": actor}
        ).execute()
