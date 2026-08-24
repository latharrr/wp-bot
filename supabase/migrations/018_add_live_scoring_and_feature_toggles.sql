-- Ported from poison-br09/whatsapp-propensity-scoring: live poll votes can now be
-- automatically scored (see app/services/scoring_normalization.py), not just CSV uploads.
alter table whatsapp_poll_vote_event add column if not exists normalized_vote integer;
alter table whatsapp_poll_vote_snapshot add column if not exists normalized_vote integer;

-- Global operator kill-switches for the two automated pipelines (keyword matching, live
-- propensity scoring) -- lets an operator pause either without disconnecting WhatsApp itself.
create table if not exists feature_toggles (
    key text primary key,
    enabled boolean not null default true,
    updated_at timestamptz not null default now()
);

insert into feature_toggles (key, enabled) values
    ('keyword_analysis', true),
    ('propensity_scoring', true)
on conflict (key) do nothing;
