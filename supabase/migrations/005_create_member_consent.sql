-- The second consent gate: an individual member's own opt-in, independent of the group-level
-- toggle in `groups.consent_status`. A contact/keyword row is only exportable when BOTH pass --
-- enforced structurally by the views in 016_create_exportable_views.sql, not by application code.
create table if not exists member_consent (
    id uuid primary key default gen_random_uuid(),
    group_jid text not null references groups (group_jid) on delete cascade,
    member_phone text not null,
    opted_in boolean not null default true,
    opt_in_method text not null check (opt_in_method in ('reply', 'reaction', 'manual_admin')),
    opt_in_message_id text,
    opted_in_at timestamptz not null default now(),
    opted_out_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (group_jid, member_phone)
);

create index if not exists idx_member_consent_group_jid on member_consent (group_jid);
create index if not exists idx_member_consent_phone on member_consent (member_phone);
