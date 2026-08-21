from dataclasses import dataclass
from typing import Optional


@dataclass
class GroupRecord:
    group_jid: str
    group_name: Optional[str]
    member_count: int
    consent_status: str  # none | consented | revoked

    def to_supabase_payload(self) -> dict:
        return {
            "group_jid": self.group_jid,
            "group_name": self.group_name,
            "member_count": self.member_count,
        }


@dataclass
class GroupMemberRecord:
    group_jid: str
    member_jid: str
    phone: Optional[str]
    display_name: Optional[str]
    is_admin: bool

    def to_supabase_payload(self) -> dict:
        return {
            "group_jid": self.group_jid,
            "member_jid": self.member_jid,
            "phone": self.phone,
            "display_name": self.display_name,
            "is_admin": self.is_admin,
        }
