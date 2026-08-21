-- Ported from the reference repo (poison-br09/whatsapp-propensity-scoring) for CSV batch scoring.
create table if not exists poll_prediction (
    id uuid primary key default gen_random_uuid(),
    mobile text not null,
    product_name text,
    poll_date date,
    vote text,
    prediction_score numeric(5, 2) not null,
    source_filename text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (mobile, source_filename)
);

create index if not exists idx_poll_prediction_mobile on poll_prediction (mobile);
