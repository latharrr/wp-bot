-- Cache/audit of keyword hits, populated as messages come in from the bridge (real-time) and
-- backfilled by keyword_search_service for retroactive searches over `messages`.
create table if not exists keyword_match (
    id uuid primary key default gen_random_uuid(),
    keyword text not null,
    group_jid text not null references groups (group_jid) on delete cascade,
    sender_jid text not null,
    sender_name text,
    sender_phone text,
    message text not null,
    message_id text not null,
    message_date timestamptz not null,
    created_at timestamptz not null default now(),
    unique (message_id, keyword)
);

create index if not exists idx_keyword_match_keyword on keyword_match (keyword);
create index if not exists idx_keyword_match_sender_phone on keyword_match (sender_phone);
create index if not exists idx_keyword_match_group_jid on keyword_match (group_jid);
