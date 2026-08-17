# Embeddable Widget & Lead-Capture Platform

A backend platform that lets customers create embeddable widgets (signup
forms, CTAs, popovers), hand out a single `<script>` tag, and safely accept
submissions from any website that embeds it -- validated, rate-limited,
spam-filtered, geo-enriched, and visible in a dashboard.

Built for the FlyRank Backend AI Engineering internship capstone.

## Architecture

Widget Owner (authenticated, JWT)
|
v
Widget Management API --------> Widget DB (Postgres, tenant-isolated)
|
v
embed snippet: <script src=".../widget.js?id=abc123"></script>

Customer Website (any origin, e.g. localhost:5500)
|
v <script src="widget.js?id=123">
|
v GET /widgets/:id/config (public, cached, CORS-open)
|
v renders form client-side

Website Visitor
|
v POST /submissions (public, CORS)
|
+--> validation ---------- bad payload? --> 4xx, never 500
|
+--> rate limit + honeypot -- flood/bot? --> 429 or silent drop
|
+--> geo enrichment: Provider A --(fails)--> Provider B --(fails)--> store anyway
|
+--> store submission
|
+--> confirmation email side effect (failure never blocks success)

Widget Owner
|
v
Dashboard API <---- submissions + stats


### Layers

app/
routers/ FastAPI route handlers -- HTTP-only concerns
services/ (business logic lives inline in routers for this
scope; see Limitations)
repositories/ all SQL/ORM queries, one module per table
models/ Pydantic schemas + SQLAlchemy models
integrations/ geo provider clients (fallback chain), notify (side effect)
middleware/ JWT auth dependency


Storage is swappable behind the repository layer without touching routes --
the same pattern proved across three earlier assignments in this track
(memory -> SQLite -> Postgres).

## Why these choices

- **PostgreSQL** over SQLite: this is a multi-tenant system meant to run as
  a real server, not a single-file dev database.
- **JWT auth**: stateless, no session storage needed, works cleanly across
  the containerized stack.
- **slowapi** for rate limiting: simplest FastAPI-native option, in-memory
  is fine for a single-instance deployment at this scope.
- **Honeypot over CAPTCHA**: zero friction for real users, catches the
  large majority of unsophisticated bots, no third-party dependency.

## How to run it

**One command, from a clean clone:**

```bash
cp .env.example .env
docker compose up
```

This builds the API image, starts Postgres, waits for it to report healthy
(via a `pg_isready` healthcheck), then starts the API. Available at
`http://localhost:8000`.

Stop everything: `docker compose down` (add `-v` to also wipe the database
and start fully fresh).

### Running tests

```bash
docker exec -it widgetdb psql -U postgres -c "CREATE DATABASE widgets_test;"
python -m pytest tests/ -v
```

(Tests run against a separate `widgets_test` database, wiped clean before
every test function, so they never touch your dev data.)

### Seeing the widget actually work cross-origin

1. With `docker compose up` running, create a widget via the API (see
   below) and note its `id`.
2. In a separate folder, create a plain `index.html` containing just:
```html
   <script src="http://localhost:8000/widget.js?id=YOUR_WIDGET_ID"></script>
```
3. Serve it on a different port: `python -m http.server 5500`
4. Open `http://localhost:5500` -- the widget renders itself from that one
   script tag, fetched cross-origin from the API.

## Environment variables

See `.env.example`. None of these are real secrets in local dev, but in a
real deployment `JWT_SECRET` and the database password would be rotated
and never committed.

DATABASE_URL=postgresql+psycopg://postgres:dev@db:5432/widgets
JWT_SECRET=changeme-to-something-random
GEO_PROVIDER_A_URL=http://ip-api.com/json
GEO_PROVIDER_B_URL=https://ipapi.co


## API reference

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /api/auth/signup | - | Create a tenant account, returns a JWT |
| POST | /api/auth/login | - | Log in, returns a JWT |

### Widget management (authenticated)
| Method | Path | Description |
|---|---|---|
| POST | /api/widgets | Create a widget |
| GET | /api/widgets | List your widgets |
| GET | /api/widgets/{id} | Get one widget |
| PUT | /api/widgets/{id} | Update a widget (bumps version) |
| DELETE | /api/widgets/{id} | Delete a widget |
| GET | /api/widgets/{id}/embed | Get the embed snippet |

### Public delivery (unauthenticated, CORS-open)
| Method | Path | Description |
|---|---|---|
| GET | /widgets/{id}/config | Widget config JSON, short cache |
| GET | /widget.js | The embed script, long cache |

### Public submission (unauthenticated, CORS-open, hardened)
| Method | Path | Description |
|---|---|---|
| OPTIONS | /submissions | CORS preflight |
| POST | /submissions | Submit a form -- validated, rate-limited, spam-checked, enriched |

### Dashboard (authenticated)
| Method | Path | Description |
|---|---|---|
| GET | /api/widgets/{id}/submissions | List a widget's submissions |
| GET | /api/widgets/{id}/stats | Counts, geo breakdown, by-day |
| GET | /api/dashboard/overview | Totals across all your widgets |

## What's hardened, and how it's proven

Every claim below has real, pasted evidence in `EVIDENCE.md`:

- **CORS**: preflight handled correctly, `access-control-allow-origin`
  present on cross-origin requests.
- **Validation**: missing required fields -> 400, unknown widget -> 404,
  oversized field values -> 413. Never a raw 500 on bad input.
- **Rate limiting**: 5 requests/minute per IP on the submission endpoint --
  6th request in a burst returns 429, legitimate traffic resumes after
  the window.
- **Spam control**: a hidden honeypot field. A filled honeypot returns a
  fake success (so a bot can't tell it was caught) but nothing is stored.
- **Geo enrichment fallback chain**: tries Provider A, then Provider B, then
  gives up gracefully. Proven with both a real live failure (Provider B's
  free tier rate-limited us mid-development) and deterministic env-var
  toggles (`FORCE_PROVIDER_A_DOWN`, `FORCE_PROVIDER_B_DOWN`).
- **Safe side effect**: a confirmation "email" (logged to console) fires
  after storage. Forcing it to throw (`FORCE_NOTIFY_DOWN=true`) still
  returns 201 -- the submission is never rolled back by a broken
  secondary action.
- **Tenant isolation**: every widget/submission query filters by both
  `id` and `tenant_id` in the same clause. Proven with a second tenant
  account attempting to read/update/delete the first tenant's data --
  always a clean 404, never a 403 (which would leak that the resource
  exists).

## Automated tests

19 pytest tests covering CORS preflight, invalid/oversized payloads,
rate limiting, the honeypot, the geo fallback chain, tenant isolation,
and widget CRUD -- run against an isolated test database, wiped before
every test. See `tests/` and `EVIDENCE.md` for full output.

## Limitations (honest)

- **No real background job queue.** Enrichment and the notify side effect
  run inline in the request, not offloaded to a worker. At this scope
  (a capstone, not production traffic) that's an acceptable tradeoff --
  a real deployment would move both to a queue so a slow geo provider
  can't add latency to the visitor-facing response.
- **No `services/` layer in practice.** The layer sketch exists in the
  folder structure, but business logic (validation, the fallback chain
  orchestration) currently lives directly in the router functions rather
  than a separate service module. Given more time, I'd extract that for
  cleaner separation.
- **Widget JS isn't a true versioned bundle.** It's served with a
  long-cache header, but the URL doesn't change when the script's content
  changes -- a customer's browser could serve a stale cached copy after
  an update. A real fix would embed a version/hash in the URL and bump it
  on release.
- **No visual widget builder.** Configuration is authored as structured
  JSON through the API, by design -- see `DESIGN.md`'s explicit non-goal.
- **Email is simulated** (logged to console), not a real SMTP send --
  what's graded and proven is that its *failure* never blocks a
  submission, not the delivery mechanism itself.

## Build log

See `BUILDLOG.md` for an honest account of where AI (Claude) helped,
where its first attempt was wrong, and what had to be fixed -- including
a passlib/bcrypt compatibility bug, a missing `email-validator` dependency,
and a rate-limiter test-isolation bug that initially looked like a broken
feature but was actually the rate limiter correctly doing its job across
test runs.