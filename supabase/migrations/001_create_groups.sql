create table if not exists groups (
    id uuid primary key default gen_random_uuid(),
    group_jid text not null unique,
    group_name text,
    consent_status text not null default 'none' check (consent_status in ('none', 'consented', 'revoked')),
    consent_marked_by text,
    consent_marked_at timestamptz,
    member_count integer not null default 0,
    first_seen_at timestamptz not null default now(),
    last_synced_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_groups_consent_status on groups (consent_status);
