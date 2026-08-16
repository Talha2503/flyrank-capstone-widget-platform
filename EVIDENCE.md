## Widget management
- [x] Authenticated CRUD endpoints reject requests without valid auth
  (see: `get_current_tenant_id` dependency raises 401 on missing/invalid token)
- [x] Multi-tenant isolation proven: tenant A cannot read/modify tenant B's data

  Created a widget as tenant A (id `3f7edef9-3324-4118-a68e-2c6fde218de3`).
  Signed up as a separate tenant B, then requested tenant A's widget using
  tenant B's token:

curl.exe -i http://localhost:8000/api/widgets/3f7edef9-3324-4118-a68e-2c6fde218de3 -H "Authorization: Bearer $token2"

HTTP/1.1 404 Not Found
{"detail":"Widget not found"}


  Tenant B gets a clean 404, not the widget and not a 403 "forbidden" (which
  would leak that the resource exists). Isolation is enforced at the query
  layer in `widget_repo.get_by_id_for_tenant`, which filters by both
  `id` AND `tenant_id` in the same WHERE clause.

  ## Public submission API
- [x] Cross-origin submissions work (CORS + preflight)

curl.exe -i -X OPTIONS http://localhost:8000/submissions -H "Origin: http://localhost:5500" -H "Access-Control-Request-Method: POST"

HTTP/1.1 200 OK
access-control-allow-origin: *
access-control-allow-methods: GET, POST, OPTIONS


- [x] Malformed/oversized payloads rejected with clean 4xx

  Missing required field -> 400: `{"detail":"Field 'email' is required"}`
  Unknown widget id -> 404: `{"detail":"Widget not found"}`
  Oversized field value (3000 chars) -> 413: `{"detail":"Field 'email' is too long"}`

- [x] Valid submissions stored, linked to correct widget + tenant

curl.exe -i -X POST http://localhost:8000/submissions ...

HTTP/1.1 201 Created
{"id":"7ca4589a-9002-40f3-9ea1-1b2631130dde","widget_id":"5e0ce3b7-7a8d-49b1-a1b2-2017733c9bd8", ...}

## Abuse protection
- [x] Rate limiting returns 429 under a burst, legit traffic still served

  Fired 6 rapid requests against the same widget:

Request 1 -> 201
Request 2 -> 201
Request 3 -> 201
Request 4 -> 201
Request 5 -> 201
Request 6 -> 429

  Limit is 5/minute per IP. After the window resets, normal requests
  succeed again (confirmed manually).

- [x] Spam control demonstrably blocks a spam submission

  Submitted with the honeypot `website` field filled in (as a bot would):

HTTP/1.1 201 Created
{"id":"00000000-0000-0000-0000-000000000000", ...}

  Response looks like success (so a bot can't detect it was caught), but
  querying the database for that submission returns 0 rows -- it was
  silently dropped before storage:

SELECT id, data FROM submissions WHERE data->>'email' = 'bot@spam.com';
id | data
----+------
(0 rows)

## Enrichment & safe side effects
- [x] Provider fallback chain: A down -> B answers

  Provider A up, real IP (8.8.8.8) -> stored with provider_a, real geo data
  (United States / Ashburn).

  While testing, provider B (ipapi.co free tier) genuinely rate-limited us
  mid-session with a real 429 -- caught in the server log:

[geo] provider_b failed: Client error '429 Too Many Requests' for url
'https://ipapi.co/8.8.8.8/json/'

  The submission still returned 201 and was stored -- proving the fallback
  chain degrades correctly even under a real, unplanned provider failure,
  not just a synthetic one.

  Also tested deterministically via FORCE_PROVIDER_A_DOWN=true env toggle:
  A forced down, B (working) picks up -> stored with provider_b.

- [x] Both providers down -> submission still succeeds, without geo

  With both FORCE_PROVIDER_A_DOWN=true and FORCE_PROVIDER_B_DOWN=true:

HTTP/1.1 201 Created

  DB row: geo_country/geo_city/geo_provider_used all null, submission
  still stored successfully. Confirms enrichment failure never blocks
  the main path.

  - [x] A failing confirmation email / webhook does not prevent the submission from being stored

  Happy path:

[notify] confirmation email sent to visitor@example.com for widget 'Newsletter Signup'
HTTP/1.1 201 Created


  Forced failure (FORCE_NOTIFY_DOWN=true, raises a real exception):

[notify] side effect failed, submission still succeeds: Simulated email provider outage
HTTP/1.1 201 Created

  Submission still returns 201 and is stored either way -- the try/except
  around the notify call happens after storage already committed, so a
  broken email provider can never turn a successful submission into a
  failed request.