-- Tracks the outcome of the manual, super_admin-only deep history backfill
-- (see app/services/backfill_service.py) so the dashboard can show, per group,
-- how far back the backfill reached and how many messages it added.
alter table groups
    add column if not exists backfill_status text check (backfill_status in ('running', 'done', 'failed')),
    add column if not exists backfill_started_at timestamptz,
    add column if not exists backfill_completed_at timestamptz,
    add column if not exists backfill_pages_fetched integer,
    add column if not exists backfill_messages_stored integer,
    add column if not exists backfill_stopped_reason text,
    add column if not exists backfill_oldest_message_at timestamptz;
