create table if not exists group_members (
    id uuid primary key default gen_random_uuid(),
    group_jid text not null references groups (group_jid) on delete cascade,
    member_jid text not null,
    phone text,
    display_name text,
    is_admin boolean not null default false,
    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (group_jid, member_jid)
);

create index if not exists idx_group_members_group_jid on group_members (group_jid);
create index if not exists idx_group_members_phone on group_members (phone);
