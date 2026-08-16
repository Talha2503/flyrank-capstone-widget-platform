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