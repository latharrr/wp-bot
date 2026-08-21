from dataclasses import dataclass
from typing import Optional


@dataclass
class ConsentPromptRecord:
    group_jid: str
    message_id: str
    prompt_text: str

    def to_supabase_payload(self) -> dict:
        return {
            "group_jid": self.group_jid,
            "message_id": self.message_id,
            "prompt_text": self.prompt_text,
            "is_active": True,
        }


@dataclass
class MemberConsentRecord:
    group_jid: str
    member_phone: str
    opted_in: bool
    opt_in_method: str  # reply | reaction | manual_admin
    opt_in_message_id: Optional[str] = None

    def to_supabase_payload(self) -> dict:
        return {
            "group_jid": self.group_jid,
            "member_phone": self.member_phone,
            "opted_in": self.opted_in,
            "opt_in_method": self.opt_in_method,
            "opt_in_message_id": self.opt_in_message_id,
        }
