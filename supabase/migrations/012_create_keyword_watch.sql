-- Lightweight, auto-upserted whenever an operator searches a term. Doubles as a "recent
-- searches" list; not required for search correctness (search always scans `messages` live).
create table if not exists keyword_watch (
    id uuid primary key default gen_random_uuid(),
    keyword text not null unique,
    is_active boolean not null default true,
    search_count integer not null default 1,
    last_searched_at timestamptz not null default now(),
    created_at timestamptz not null default now()
);
