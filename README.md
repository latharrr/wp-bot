# wp-bot

A WhatsApp community dashboard for a business's own groups: live pairing-code login, a poll
viewer with voter breakdown, consent-gated group contact export, keyword search across
messages, and CSV batch propensity scoring. Successor to
[`poison-br09/whatsapp-propensity-scoring`](https://github.com/poison-br09/whatsapp-propensity-scoring),
carrying forward its bridge/scoring pipeline and adding a dashboard on top.

## Consent model (read this before deploying)

Contact and keyword-match data for a person is only ever exportable when **both**:

1. The **group** has been explicitly marked "consented" by the operator in the dashboard, and
2. That **individual member** has separately opted in (replying/reacting to a consent-prompt
   message the bot posts, or a manual admin override for verbal consent).

Both gates are enforced in the database itself via the `exportable_contacts` and
`exportable_keyword_matches` views (`supabase/migrations/016_create_exportable_views.sql`) — the
application code for every export/detail endpoint reads only from these views, never from the
raw `group_members` / `keyword_match` tables. Do not add a code path that bypasses them.

Poll voter breakdowns use the group-level gate only (poll votes are already visible to everyone
in the group natively); non-consented groups only ever get aggregate counts, never named voters.

## Requirements

- Python 3.11+
- Node 20+
- A Supabase project

## Setup

1. Copy `.env.example` to `.env` and fill in the values (Supabase credentials, a strong
   `JWT_SECRET`, `WHATSAPP_INTERNAL_TOKEN`, `WHATSAPP_BRIDGE_CONTROL_TOKEN`).
2. Run the migrations in `supabase/migrations/` in order against your Supabase project.
3. Install Python deps: `python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"`
4. Install bridge deps: `cd whatsapp_bridge && npm install && cd ..`
5. Install dashboard deps: `cd dashboard && npm install && cd ..`
6. Create the operator account: `.venv/bin/python scripts/create_admin.py <username> <password>`

## Run locally

```bash
# terminal 1
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# terminal 2
cd dashboard && npm run dev
```

With `WHATSAPP_BRIDGE_ENABLED=true`, the API spawns the bridge subprocess automatically on
startup. Open the dashboard, log in, and go to **Connection** to pair a WhatsApp number.

## Run with Docker

```bash
docker compose up --build
```

## Architecture

- `app/` — FastAPI backend: auth, groups, consent workflow, poll ingestion, CSV scoring,
  keyword search, exports.
- `whatsapp_bridge/` — Node/TypeScript Baileys process the API manages as a subprocess; handles
  pairing, group/contact sync, poll detection, message/reaction forwarding.
- `dashboard/` — Next.js operator dashboard.
- `supabase/migrations/` — numbered SQL migrations, including the consent-enforcing views.

See the code comments in `app/services/consent_service.py` and
`supabase/migrations/016_create_exportable_views.sql` for the consent-gating mechanics in detail.
