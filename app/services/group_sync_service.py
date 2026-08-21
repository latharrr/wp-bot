from app.models.group import GroupMemberRecord
from app.models.whatsapp import GroupsSyncRequest
from app.repositories.supabase_group_repository import SupabaseGroupRepository


class GroupSyncService:
    def __init__(self) -> None:
        self._groups = SupabaseGroupRepository()

    def sync(self, payload: GroupsSyncRequest) -> None:
        for group in payload.groups:
            self._groups.upsert_group(group.group_jid, group.subject, len(group.participants))
            members = [
                GroupMemberRecord(
                    group_jid=group.group_jid,
                    member_jid=p.jid,
                    phone=p.phone,
                    display_name=p.display_name,
                    is_admin=p.is_admin,
                )
                for p in group.participants
            ]
            self._groups.upsert_members(group.group_jid, members)


def get_group_sync_service() -> GroupSyncService:
    return GroupSyncService()
