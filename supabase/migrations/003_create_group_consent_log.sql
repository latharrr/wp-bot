-- Append-only audit trail of consent state changes. Durable even if `groups.consent_status`
-- (a mutable field) is ever changed by hand -- this is the record of who did what, when.
create table if not exists group_consent_log (
    id uuid primary key default gen_random_uuid(),
    group_jid text not null references groups (group_jid) on delete cascade,
    action text not null check (action in ('requested', 'consented', 'revoked')),
    actor text not null,
    occurred_at timestamptz not null default now()
);

create index if not exists idx_group_consent_log_group_jid on group_consent_log (group_jid);
