# Design — Embeddable Widget & Lead-Capture Platform

## Problem
Let a customer define a widget (signup form, CTA, popover), hand them one
`<script>` tag, and safely accept submissions from any website that embeds
it — validated, rate-limited, spam-filtered, geo-enriched, and visible in
a dashboard.

## Data model

### Tenant
- id (uuid, pk)
- email (text, unique)
- password_hash (text)
- created_at (timestamptz)

### Widget
- id (uuid, pk)
- tenant_id (uuid, fk -> Tenant.id, indexed)
- type (text: signup_form | cta | popover)
- title (text)
- description (text, nullable)
- fields (jsonb — array of {name, label, type, required})
- button_text (text)
- display (jsonb — {color, position, delay_seconds, ...})
- version (int, default 1 — bumped on every config change, drives cache-busting)
- created_at / updated_at (timestamptz)

### Submission
- id (uuid, pk)
- widget_id (uuid, fk -> Widget.id, indexed)
- tenant_id (uuid, fk -> Tenant.id, indexed — denormalized for fast isolation queries)
- data (jsonb — visitor's submitted field values)
- ip_address (text)
- geo_country / geo_city (text, nullable)
- geo_provider_used (text, nullable: provider_a | provider_b | null)
- spam_flagged (boolean, default false)
- idempotency_key (text, unique, nullable)
- created_at (timestamptz, indexed — for time-series stats)

## The embed flow
1. Owner creates a Widget via the authenticated API
2. API returns an embed snippet: `<script src=".../widget.js?id={widget.id}"></script>`
3. Customer pastes that script tag into their site
4. Browser loads `widget.js` (versioned, long-cache)
5. `widget.js` fetches `GET /widgets/{id}/config` (short-cache, public, CORS-open)
6. `widget.js` renders the form using that config
7. Visitor submits -> `POST /submissions` (public, CORS, validated, rate-limited, spam-checked)
8. Submission is enriched (geo) and stored
9. A side effect fires (confirmation email/webhook) -- failure here never blocks step 8's success
10. Owner sees it in the dashboard API

## API contracts

### 1. Widget Management API -- authenticated (JWT bearer token)
- POST   /api/auth/signup
- POST   /api/auth/login
- POST   /api/widgets
- GET    /api/widgets
- GET    /api/widgets/{id}
- PUT    /api/widgets/{id}
- DELETE /api/widgets/{id}
- GET    /api/widgets/{id}/embed -> { snippet: "<script ...>" }

### 2. Public delivery -- public, cached, CORS-open
- GET /widget.js -> versioned JS bundle, long cache
- GET /widgets/{id}/config -> JSON config, short cache

### 3. Public submission -- public, CORS, hardened
- OPTIONS /submissions -> CORS preflight
- POST /submissions -> validated, rate-limited, spam-checked, enriched, stored

### 4. Dashboard API -- authenticated
- GET /api/widgets/{id}/submissions
- GET /api/widgets/{id}/stats -> counts over time, geo breakdown
- GET /api/dashboard/overview -> across all of the tenant's widgets

## Layer sketch

app/
routers/ <- FastAPI route handlers, HTTP-only concerns
services/ <- business logic, enrichment fallback chain, rate-limit decisions
repositories/ <- all SQL, one module per table, only place that touches the DB
models/ <- Pydantic schemas + SQLAlchemy models
integrations/ <- geo provider clients (A + B), email/webhook sender
middleware/ <- CORS config, rate limiter, auth dependency


## Auth approach
Email/password signup + JWT bearer token for the Widget Management API and
Dashboard API. The public config and submission endpoints stay unauthenticated
by design -- visitors on sites we don't control need to reach them. The widget
`id` is the only "credential" on those routes; tenant isolation is enforced at
the query layer (`WHERE tenant_id = ?` on every query), never trusted from
client input.

## Non-goal
This capstone does not build a visual drag-and-drop widget designer. Widget
configuration (fields, display options) is authored as structured JSON through
the API. A real product would eventually add a no-code builder UI on top of
this, but that's out of scope here -- the grade lives in the backend, not the
widget's visual design.