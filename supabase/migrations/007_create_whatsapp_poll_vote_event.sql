-- Append-only raw vote log; deduplicated on insert via dedupe_key, never overwritten.
create table if not exists whatsapp_poll_vote_event (
    id uuid primary key default gen_random_uuid(),
    dedupe_key text not null unique,
    group_jid text not null references groups (group_jid) on delete cascade,
    poll_message_id text not null references whatsapp_poll (poll_message_id) on delete cascade,
    poll_title text,
    voter_jid text not null,
    voter_phone text,
    voter_name text,
    selected_options jsonb not null default '[]'::jsonb,
    vote_timestamp timestamptz not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_poll_vote_event_poll_message_id on whatsapp_poll_vote_event (poll_message_id);
create index if not exists idx_poll_vote_event_voter_phone on whatsapp_poll_vote_event (voter_phone);
