create table if not exists export_audit_log (
    id uuid primary key default gen_random_uuid(),
    actor text not null,
    export_type text not null check (export_type in ('contacts', 'poll', 'keyword')),
    group_jid text,
    keyword text,
    row_count integer not null default 0,
    filename text not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_export_audit_log_created_at on export_audit_log (created_at desc);
