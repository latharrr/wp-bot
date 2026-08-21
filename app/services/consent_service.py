"""The single place both consent gates (group-level toggle + per-member opt-in) are managed.

Nothing outside this service should write to `groups.consent_status` or `member_consent`.
Reads of "is this exportable" always go through the repository's exportable_* view methods,
which enforce the gates in SQL regardless of what this service does -- this service is about
the *workflow* (request -> opt-in -> mark consented -> revoke), the views are the backstop.
"""
import logging
from typing import Optional

from app.core.bridge_control_client import get_bridge_control_client
from app.models.consent import ConsentPromptRecord, MemberConsentRecord
from app.repositories.supabase_consent_repository import SupabaseConsentRepository
from app.repositories.supabase_group_repository import SupabaseGroupRepository

logger = logging.getLogger(__name__)

DEFAULT_PROMPT_TEMPLATE = (
    "Hi! We'd like to keep a record of your number and messages you send in this group for our "
    "own records and analytics. Reply YES or react ✅ to this message to agree. "
    "You can opt out any time by messaging us."
)


class ConsentService:
    def __init__(self) -> None:
        self._groups = SupabaseGroupRepository()
        self._consent = SupabaseConsentRepository()

    async def request_consent(self, group_jid: str, actor: str, prompt_text: Optional[str] = None) -> str:
        text = prompt_text or DEFAULT_PROMPT_TEMPLATE
        message_id = await get_bridge_control_client().send_message(group_jid, text)
        self._consent.create_prompt(ConsentPromptRecord(group_jid=group_jid, message_id=message_id, prompt_text=text))
        self._groups.log_consent_requested(group_jid, actor)
        return message_id

    def mark_group_consented(self, group_jid: str, actor: str) -> None:
        self._groups.set_consent_status(group_jid, "consented", actor)

    def revoke_group_consent(self, group_jid: str, actor: str) -> None:
        self._groups.set_consent_status(group_jid, "revoked", actor)

    def get_member_consent_progress(self, group_jid: str) -> list[dict]:
        return self._consent.list_member_consent(group_jid)

    def manual_opt_in(self, group_jid: str, member_phone: str) -> None:
        self._consent.record_opt_in(
            MemberConsentRecord(
                group_jid=group_jid,
                member_phone=member_phone,
                opted_in=True,
                opt_in_method="manual_admin",
            )
        )

    def manual_opt_out(self, group_jid: str, member_phone: str) -> None:
        self._consent.record_opt_out(group_jid, member_phone)

    def handle_reply(self, group_jid: str, reply_to_message_id: Optional[str], sender_phone: Optional[str]) -> bool:
        """Called from the /internal/whatsapp/message webhook. Returns True if this reply
        opted the sender into consent (matched an active prompt in their group)."""
        if not reply_to_message_id or not sender_phone:
            return False
        prompt = self._consent.get_active_prompt_by_message_id(reply_to_message_id)
        if not prompt or prompt["group_jid"] != group_jid:
            return False
        self._consent.record_opt_in(
            MemberConsentRecord(
                group_jid=group_jid,
                member_phone=sender_phone,
                opted_in=True,
                opt_in_method="reply",
                opt_in_message_id=reply_to_message_id,
            )
        )
        logger.info("Recorded consent opt-in via reply: group=%s phone=%s", group_jid, sender_phone)
        return True

    def handle_reaction(self, group_jid: str, target_message_id: str, reactor_phone: Optional[str]) -> bool:
        """Called from the /internal/whatsapp/reaction webhook."""
        if not reactor_phone:
            return False
        prompt = self._consent.get_active_prompt_by_message_id(target_message_id)
        if not prompt or prompt["group_jid"] != group_jid:
            return False
        self._consent.record_opt_in(
            MemberConsentRecord(
                group_jid=group_jid,
                member_phone=reactor_phone,
                opted_in=True,
                opt_in_method="reaction",
                opt_in_message_id=target_message_id,
            )
        )
        logger.info("Recorded consent opt-in via reaction: group=%s phone=%s", group_jid, reactor_phone)
        return True


def get_consent_service() -> ConsentService:
    return ConsentService()
