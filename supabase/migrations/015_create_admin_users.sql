-- Single-operator auth. Seed via scripts/create_admin.py, not self-service signup.
create table if not exists admin_users (
    id uuid primary key default gen_random_uuid(),
    username text not null unique,
    password_hash text not null,
    created_at timestamptz not null default now()
);
