# wp-bot

A WhatsApp community dashboard for a business's own groups: live QR-code login, a poll
viewer with voter breakdown, consent-gated group contact export, keyword search across
messages, and CSV batch propensity scoring. Successor to
[`poison-br09/whatsapp-propensity-scoring`](https://github.com/poison-br09/whatsapp-propensity-scoring),
carrying forward its bridge/scoring pipeline and adding a dashboard on top.

## Consent model (read this before deploying)

There are two tiers of gating, depending on what the data is being used for:

**Contacts** (building an external outreach list) use the strict **double gate** — a person's
name/phone is only ever exportable when **both**:

1. The **group** has been explicitly marked "consented" by the operator in the dashboard, and
2. That **individual member** has separately opted in — via a manual admin override for verbal
   consent (single or bulk, from the group's Overview tab).

This gate is enforced in the database itself via the `exportable_contacts` view
(`supabase/migrations/016_create_exportable_views.sql`) — the contacts export/detail endpoints
read only from this view, never from the raw `group_members` table. Do not add a code path that
bypasses it.

**Poll voter breakdowns, keyword-match search, and the group Messages monitor** use a looser
**group-only gate**: once the group itself is marked consented, no per-member opt-in is required
to see names, phone numbers, and message content for that group. The reasoning (confirmed
explicitly by the operator): this content — who voted for what, who said what, when — is already
visible to everyone in the group natively; the group's own consent is what authorizes recording
and monitoring it, not each member's individual opt-in. That's a materially different action from
compiling an external contact list, which is why contacts keeps the stricter double gate.
Non-consented groups only ever get aggregate counts (vote tallies, hidden-match counts, total
message counts) — never named/attributed rows. See
`app/repositories/supabase_keyword_repository.py`'s `list_matches_in_consented_groups` docstring
and `app/api/v1/routes/group_messages.py` for where this is implemented.

## Live propensity scoring, keyword watchlist, and automation switches

Ported from [`poison-br09/whatsapp-propensity-scoring`](https://github.com/poison-br09/whatsapp-propensity-scoring)
(the predecessor this project already carried forward the scoring heuristic from):

- **Live scoring** — a "yes" vote on a poll whose two options map to a recognizable yes/no pair
  (`app/services/vote_normalization.py`'s token dictionary: "yes/interested/buy" vs
  "no/skip/not interested", etc.) is scored the instant it arrives, the same way a CSV row is —
  no manual export/upload needed. Still requires the voter's phone to be resolvable (see the
  `@lid` notes above) and only fires for the "yes" side (a "no" has no propensity to project).
- **Keyword watchlist** (Keyword Search page → "Watched keywords" tab) — explicitly add/enable/
  disable/delete keywords that get checked against every incoming message continuously, instead
  of only ever being backfilled reactively when someone runs a search.
- **Automation switches** (Admin page) — pause keyword matching or live scoring globally without
  disconnecting WhatsApp. Gated by the dashboard's own super_admin JWT rather than an API key
  baked into the frontend build, unlike the reference repo's version of this (see
  `app/api/v1/routes/feature_toggles.py`).
- **Poll history recovery** — if a vote arrives referencing a poll-creation message the bridge
  never saw live (e.g. it restarted mid-poll), it makes one on-demand Baileys history-sync
  request anchored at the vote to try to recover it (`whatsapp_bridge/src/handlers/polls.ts`).
  This is a deliberately scoped-down port of the reference repo's continuous background backfill
  system — reactive and bounded to one request per occurrence, not a standing job that
  re-scrapes every group's history on every reconnect. It also can't work miracles: WhatsApp only
  syncs so much history to a linked device, so very old votes still won't be recoverable.
- **All Polls page** (nav) — a paginated, cross-group poll listing distinct from a single group's
  own Polls tab, with an optional `group_jid` filter, matching the reference repo's admin view.

**Not ported:** the reference repo's core architecture is fully multi-tenant — every registered
user pairs their own separate WhatsApp number through their own dedicated bridge process. This
app deliberately keeps the original single-business-connection model instead (one bridge, staff
differentiated by dashboard *feature* access, not by *which WhatsApp number* they own) since
converting to per-user bridges is a fundamental product-shape change, not a portable feature —
it would mean redesigning the consent model around multiple simultaneous bridges and carries
real risk to an already-paired live session. Ask for it explicitly as a separate, deliberate
project if you actually need multiple independent WhatsApp numbers under one dashboard.

## Users and roles

There are two roles:

- **super_admin** — one account, created via `scripts/create_admin.py` (never through the
  dashboard). Sees every feature and manages other users from the **Admin** page: create a
  user, delete a user, and toggle which features (`connection`, `groups`, `keyword_search`,
  `csv_scoring`, `export_log`) they can see.
- **user** — created by the super_admin, sees only the features granted to them. Both the
  dashboard nav and every API route enforce this independently (`app/api/deps.py`'s
  `require_feature(...)`, applied per-router) — hiding a nav link is a UX nicety, not the
  actual security boundary.

Feature grants take effect on a user's very next request, not after their token expires:
`get_current_user` looks the account back up by username on every request rather than trusting
role/features baked into the JWT.

## Security notes

- The app **refuses to start** if `API_KEY`, `JWT_SECRET`, `WHATSAPP_INTERNAL_TOKEN`, or
  `WHATSAPP_BRIDGE_CONTROL_TOKEN` are still at their `.env.example` placeholder value (see
  `Settings.insecure_defaults_still_in_use` in `app/core/config.py`) — those placeholders are
  public since this repo is, so leaving one unset means anyone can forge a valid session.
- `CORS_ALLOWED_ORIGINS` defaults to `*` for local dev; set it to your actual dashboard origin(s)
  in production.
- Login is rate-limited (5 failed attempts / 15 min per username, in-memory — see
  `app/core/rate_limit.py`). This is a single-process limiter; it won't hold up if you ever run
  more than one API instance behind a load balancer.
- `/internal/whatsapp/*` (the bridge's webhooks) requires both a shared-secret token and that the
  request came from loopback (`app/api/deps.py`'s `require_loopback_client`) — defense in depth
  since it shares the same public port as the dashboard API in the default docker-compose setup.
- **Using Baileys (or any unofficial WhatsApp client) is against WhatsApp's Terms of Service.**
  No amount of careful engineering in this repo eliminates the risk of WhatsApp detecting and
  banning/restricting the connected number — that's a platform-level risk inherent to the
  approach, not a bug. What this codebase does do to reduce (not eliminate) that risk:
  - Never sends bulk/automated messages into groups (the earlier consent-request-message flow
    was removed entirely; the bridge is now purely a passive listener plus manual QR pairing).
  - Debounces full-account group resyncs to once per 5 minutes (`FULL_GROUP_SYNC_COOLDOWN_MS` in
    `whatsapp_bridge/bridge.ts`) so a flaky-network reconnect storm doesn't look like repeated
    bulk scraping of every group's membership.
  - Waits 3s before reconnecting after any disconnect, rather than hammering WhatsApp's servers
    immediately.
  - If you can't afford to lose the number, use the official WhatsApp Business Platform (Cloud
    API) instead — it requires business verification but carries no ban risk for correct usage.

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
6. Create the super admin account: `.venv/bin/python scripts/create_admin.py <username> <password>`
   — this is the only account created outside the dashboard; create everyone else from its
   Admin page.

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

- `app/` — FastAPI backend: auth, roles/feature access, groups, consent workflow, poll
  ingestion, CSV scoring, keyword search, exports.
- `whatsapp_bridge/` — Node/TypeScript Baileys process the API manages as a subprocess; handles
  pairing, group/contact sync, poll detection, message/reaction forwarding.
- `dashboard/` — Next.js operator dashboard.
- `supabase/migrations/` — numbered SQL migrations, including the consent-enforcing views.

See the code comments in `app/services/consent_service.py` and
`supabase/migrations/016_create_exportable_views.sql` for the consent-gating mechanics in detail.
