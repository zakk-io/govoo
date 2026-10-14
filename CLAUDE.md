# Project Instructions — Govoo

## User-facing text must never leak internal/technical details

Anything a real user (Company Secretary, Director, Shareholder, Auditor) actually
sees in the running app — field `help=` text, view `string=` labels/section
headers, error messages (`ValidationError`/`UserError`), email subjects/bodies,
dashboard labels — must read like plain business language, with zero developer
traceability artifacts in it. Specifically, never put any of these in a
user-visible string:

- **GitHub issue numbers**, e.g. `"Voting Workflow (issue #269)"`,
  `"Issue #271: when enabled..."`.
- **Raw `ir.config_parameter` technical keys** inside exception messages, e.g.
  `'... ("govoo_board.resolution_notice_period_days") requires...'`. Refer to
  the setting by its plain Governance Settings label instead (e.g. "the
  configured notice period in Governance Settings"), never by its internal
  key.
- **Business-rule codes, spec references, or bracket markers** such as
  `BR-BOARD-005`, `open-decisions.md item 11`, or `[CONFIRM]` — these belong in
  Python code comments/docstrings for developers, never in `help=` text,
  `string=` labels, or exception messages a user will actually read.

When a field or check genuinely needs a "this is a legal/compliance threshold,
confirm with your legal team before relying on it" caveat, say exactly that in
plain words in the user-facing text — keep the `[CONFIRM]`/issue-number/BR-code
traceability in a nearby code comment instead, not in the string the user sees.

This applies to every new config-gated check or UI element going forward, not
just a one-time cleanup: write the user-facing string in plain business
language first, then put any technical/traceability detail in a code comment.
