import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.deps import require_internal_token
from app.models.whatsapp import (
    GroupsSyncRequest,
    MessagePayload,
    PollCreatedPayload,
    PollVotePayload,
    ReactionPayload,
    SessionEventPayload,
)
from app.repositories.supabase_keyword_repository import SupabaseKeywordRepository
from app.services.consent_service import get_consent_service
from app.services.email_service import send_logout_alert
from app.services.group_sync_service import get_group_sync_service
from app.services.keyword_search_service import get_keyword_search_service
from app.services.whatsapp_poll_ingestion_service import get_poll_ingestion_service
from app.services.whatsapp_session_state import get_session_state

router = APIRouter(prefix="/internal/whatsapp", tags=["internal"], dependencies=[Depends(require_internal_token)])
logger = logging.getLogger(__name__)


@router.post("/session-event")
def session_event(payload: SessionEventPayload) -> dict:
    get_session_state().apply_event(payload.event, payload.phone_number, payload.status_code)
    if payload.event == "logged_out":
        send_logout_alert(payload.phone_number, payload.status_code)
    return {"ok": True}


@router.post("/groups-sync")
def groups_sync(payload: GroupsSyncRequest) -> dict:
    get_group_sync_service().sync(payload)
    return {"ok": True, "group_count": len(payload.groups)}


@router.post("/poll-created")
def poll_created(payload: PollCreatedPayload) -> dict:
    get_poll_ingestion_service().handle_poll_created(payload)
    return {"ok": True}


@router.post("/poll-vote")
def poll_vote(payload: PollVotePayload) -> dict:
    get_poll_ingestion_service().handle_poll_vote(payload)
    return {"ok": True}


@router.post("/message")
def message(payload: MessagePayload) -> dict:
    keyword_repo = SupabaseKeywordRepository()
    sent_at = datetime.fromtimestamp(payload.message_timestamp_ms / 1000, tz=timezone.utc).isoformat()
    message_row = {
        "group_jid": payload.group_jid,
        "group_name": payload.group_name,
        "message_id": payload.message_id,
        "sender_jid": payload.sender_jid,
        "sender_phone": payload.sender_phone,
        "sender_name": payload.sender_name,
        "message_text": payload.message,
        "reply_to_message_id": payload.reply_to_message_id,
        "sent_at": sent_at,
    }
    keyword_repo.store_message(message_row)

    active_keywords = [w["keyword"] for w in keyword_repo.list_recent_watches(limit=200) if w.get("is_active", True)]
    if active_keywords:
        get_keyword_search_service().check_message_for_keywords(active_keywords, message_row)

    consent_opt_in = get_consent_service().handle_reply(
        payload.group_jid, payload.reply_to_message_id, payload.sender_phone
    )

    return {"ok": True, "consent_opt_in": consent_opt_in}


@router.post("/reaction")
def reaction(payload: ReactionPayload) -> dict:
    consent_opt_in = get_consent_service().handle_reaction(
        payload.group_jid, payload.target_message_id, payload.reactor_phone
    )
    return {"ok": True, "consent_opt_in": consent_opt_in}
