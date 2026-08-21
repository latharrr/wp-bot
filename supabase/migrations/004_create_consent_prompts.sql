create table if not exists consent_prompts (
    id uuid primary key default gen_random_uuid(),
    group_jid text not null references groups (group_jid) on delete cascade,
    message_id text not null unique,
    prompt_text text not null,
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);

-- Only one active outstanding prompt per group at a time.
create unique index if not exists idx_consent_prompts_one_active_per_group
    on consent_prompts (group_jid)
    where is_active;

create index if not exists idx_consent_prompts_message_id on consent_prompts (message_id);
