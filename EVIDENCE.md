# Evidence

One pasted proof per Definition-of-Done checkbox from the capstone brief §6.
Filled in as each piece is built and verified -- not all at once at the end.

## Widget management
- [ ] Authenticated CRUD endpoints reject requests without valid auth
- [ ] Multi-tenant isolation proven: tenant A cannot read/modify tenant B's data

## Widget delivery
- [ ] Embed snippet generated per widget
- [ ] Public config endpoint has correct HTTP cache headers
- [ ] Widget JS served as a versioned bundle
- [ ] Widget renders on a page from a different origin

## Public submission API
- [ ] Cross-origin submissions work (CORS + preflight)
- [ ] Malformed/oversized payloads rejected with clean 4xx
- [ ] Valid submissions stored, linked to correct widget + tenant

## Abuse protection
- [ ] Rate limiting returns 429 under a burst, legit traffic still served
- [ ] Spam control demonstrably blocks a spam submission

## Enrichment & safe side effects
- [ ] Provider fallback chain: A down -> B answers
- [ ] Both providers down -> submission still succeeds, no geo
- [ ] Failing email/webhook does not block submission success

## Tests & documentation
- [ ] Automated tests cover CORS, invalid payload, oversized payload, rate limit, spam, fallback, rendering
- [ ] README has architecture diagram, setup instructions, API docs