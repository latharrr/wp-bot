"""Pydantic request bodies for the internal bridge -> Python webhooks."""
from typing import Optional

from pydantic import BaseModel


class SessionEventPayload(BaseModel):
    event: str  # connecting | connected | disconnected | logged_out
    phone_number: Optional[str] = None
    status_code: Optional[int] = None
    occurred_at_ms: Optional[int] = None


class GroupParticipantPayload(BaseModel):
    jid: str
    phone: Optional[str] = None
    display_name: Optional[str] = None
    is_admin: bool = False


class GroupSyncPayload(BaseModel):
    group_jid: str
    subject: str
    participants: list[GroupParticipantPayload]


class GroupsSyncRequest(BaseModel):
    groups: list[GroupSyncPayload]


class PollCreatedPayload(BaseModel):
    group_jid: str
    group_name: Optional[str] = None
    poll_message_id: str
    poll_title: str
    poll_options: list[str]
    poll_created_at_ms: int


class PollVotePayload(BaseModel):
    dedupe_key: str
    group_jid: str
    poll_message_id: str
    poll_title: str
    poll_options: list[str]
    voter_jid: str
    voter_phone: Optional[str] = None
    voter_name: Optional[str] = None
    selected_options: list[str]
    vote_timestamp_ms: int


class MessagePayload(BaseModel):
    group_jid: str
    group_name: Optional[str] = None
    sender_jid: str
    sender_phone: Optional[str] = None
    sender_name: Optional[str] = None
    message: str
    message_id: str
    message_timestamp_ms: int
    reply_to_message_id: Optional[str] = None


class ReactionPayload(BaseModel):
    group_jid: str
    reactor_jid: str
    reactor_phone: Optional[str] = None
    target_message_id: str
    emoji: str
    timestamp_ms: int
