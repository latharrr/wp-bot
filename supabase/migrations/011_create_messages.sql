create extension if not exists pg_trgm;

-- Full append-only message store, needed for retroactive keyword search and for resolving
-- sender phone/name when a reply is matched against an active consent prompt.
create table if not exists messages (
    id uuid primary key default gen_random_uuid(),
    group_jid text not null references groups (group_jid) on delete cascade,
    group_name text,
    message_id text not null unique,
    sender_jid text not null,
    sender_phone text,
    sender_name text,
    message_text text not null,
    reply_to_message_id text,
    sent_at timestamptz not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_messages_group_jid on messages (group_jid);
create index if not exists idx_messages_reply_to on messages (reply_to_message_id);
create index if not exists idx_messages_text_trgm on messages using gin (message_text gin_trgm_ops);
