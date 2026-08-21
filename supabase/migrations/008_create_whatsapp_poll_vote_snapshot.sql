-- Latest vote per (poll, voter). Later vote changes overwrite this snapshot in place; the
-- full history is still retained in whatsapp_poll_vote_event.
create table if not exists whatsapp_poll_vote_snapshot (
    id uuid primary key default gen_random_uuid(),
    group_jid text not null references groups (group_jid) on delete cascade,
    poll_message_id text not null references whatsapp_poll (poll_message_id) on delete cascade,
    poll_title text,
    voter_jid text not null,
    voter_phone text,
    voter_name text,
    selected_options jsonb not null default '[]'::jsonb,
    last_vote_timestamp timestamptz not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (poll_message_id, voter_jid)
);

create index if not exists idx_poll_vote_snapshot_poll_message_id on whatsapp_poll_vote_snapshot (poll_message_id);
