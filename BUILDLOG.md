# Build Log

Honest log of where AI (Claude) helped while building this, where it was
wrong, and what I changed. Updated as I go, not backfilled at the end.

## Phase 1 — Design
- Claude drafted the initial data model and API contract based on the
  capstone brief. I reviewed it against the brief's requirements and
  approved it as-is -- no changes needed at this stage.

## Phase 2 — Auth
- Claude wrote the initial auth module using passlib for password hashing.
  It broke at runtime: passlib's bcrypt backend has a known compatibility
  bug with newer bcrypt versions (`AttributeError: module 'bcrypt' has no
  attribute '__about__'`), followed by a "password cannot be longer than
  72 bytes" error even for a short password. Fixed by dropping passlib
  and calling the `bcrypt` library directly instead -- same function
  signatures, no other code needed to change. Also had to separately
  install `pydantic[email]` since `EmailStr` isn't bundled with base
  pydantic.