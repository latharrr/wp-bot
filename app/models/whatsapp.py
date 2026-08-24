"""Pydantic request bodies for the internal bridge -> Python webhooks."""

from pydantic import BaseModel


class SessionEventPayload(BaseModel):
    event: str  # connecting | connected | disconnected | logged_out
    phone_number: str | None = None
    status_code: int | None = None
    occurred_at_ms: int | None = None


class GroupParticipantPayload(BaseModel):
    jid: str
    phone: str | None = None
    display_name: str | None = None
    is_admin: bool = False


class GroupSyncPayload(BaseModel):
    group_jid: str
    subject: str
    participants: list[GroupParticipantPayload]


class GroupsSyncRequest(BaseModel):
    groups: list[GroupSyncPayload]


class PollCreatedPayload(BaseModel):
    group_jid: str
    group_name: str | None = None
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
    voter_phone: str | None = None
    voter_name: str | None = None
    selected_options: list[str]
    vote_timestamp_ms: int


class MessagePayload(BaseModel):
    group_jid: str
    group_name: str | None = None
    sender_jid: str
    sender_phone: str | None = None
    sender_name: str | None = None
    message: str
    message_id: str
    message_timestamp_ms: int
    reply_to_message_id: str | None = None


class ReactionPayload(BaseModel):
    group_jid: str
    reactor_jid: str
    reactor_phone: str | None = None
    target_message_id: str
    emoji: str
    timestamp_ms: int
