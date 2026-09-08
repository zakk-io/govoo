# Portal Security

Source: §6.3 of the source spec.

## 1. Core rule
Portal users have **no internal licence**. Expose records via `portal.mixin`,
`_compute_access_url`, and controllers. **Never expose by URL guessing — use access tokens and the
record rules above** (verbatim source instruction, §6.3).

## 2. What this means concretely for every portal-exposed model
Portal-exposed models: `govoo.meeting`, `govoo.agenda.item`, `govoo.board.pack`, `govoo.minutes`,
`govoo.resolution`, `govoo.vote`, `govoo.share.holding`, `govoo.register.member` (own record read).

For each:
1. Inherit `portal.mixin`.
2. Implement `_compute_access_url()` to build the portal URL for the record.
3. The portal controller serving that URL must check, in this order:
   a. The requesting user is authenticated as a portal user (or has a valid token for
      unauthenticated share links, if that pattern is used — `[CONFIRM]` whether unauthenticated
      token-only sharing is in scope; source implies authenticated portal users primarily).
   b. The record's access token (if unauthenticated flow is used) or the user's session matches.
   c. **The record rule (`security/record-rules.md`) still applies** — a valid token does not
      bypass the record rule; both checks are required (defense in depth, source §6.3 combining
      "access tokens **and** the record rules above").
4. A request that fails any check returns a standard "not found" / "access denied" response — it
   must not leak whether a record with that ID exists for a different company/committee/
   shareholder (avoid ID-enumeration information leakage).

## 3. Anti-patterns explicitly forbidden
- Relying on an unguessable-looking sequential ID as the only protection (URL guessing risk,
  explicitly named in source).
- Hiding a menu item / view button for an unauthorized action while leaving the underlying
  controller/route reachable without a matching record-rule check (UI hiding is a convenience, not
  a control — see `security/access-control.md` §4 note and AC-07 in
  `requirements/acceptance-criteria.md`).
- Issuing a portal access token that never expires or is not scoped to a single record
  `[RECOMMENDED — Odoo's standard `portal.mixin` token mechanism already scopes per record; do not
  build a custom broader-scoped token scheme]`.

## 4. Testing requirement
Every portal-exposed model must have at least one test proving that a portal user cannot access a
record outside their scope by direct URL/ID manipulation, in addition to the record-rule unit test.
See `testing/security-tests.md` TC-SEC-005, TC-SEC-006, and acceptance scenario AC-07.

## 5. Relationship to non-functional security (source §10.2)
Portal access sits alongside (not instead of) the broader non-functional security requirements:
MFA/SSO for internal users, access tokens for portal, encryption in transit/at rest, and a
pre-go-live penetration test that should explicitly include portal record-rule/token bypass
attempts. See `devops/environments.md` and `testing/security-tests.md`.
