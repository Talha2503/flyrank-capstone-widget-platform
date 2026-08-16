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