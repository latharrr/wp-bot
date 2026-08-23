-- Multi-user auth: one super_admin (seeded via scripts/create_admin.py) who creates additional
-- 'user' accounts from the dashboard and controls which dashboard features each one can see.
-- A super_admin always has every feature regardless of allowed_features (see app/api/deps.py).
alter table admin_users
    add column if not exists role text not null default 'user' check (role in ('super_admin', 'user')),
    add column if not exists allowed_features text[] not null default '{}';
