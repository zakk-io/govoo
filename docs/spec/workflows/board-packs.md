# Workflow: Board Packs

Source: §7.4.3. Requirement: FR-BOARD-003. Model: `govoo.board.pack`.

## Actor
Company Secretary (compile/distribute); attendees/Director Portal users (receive).

## Trigger
Secretary compiles/distributes the pack ahead of a scheduled meeting.

## Steps
1. Secretary triggers `action_compile_pack()` on the meeting (or on a new `govoo.board.pack`
   record linked to the meeting).
2. System merges the meeting's agenda items and their attached documents into one QWeb-generated
   PDF, in `sequence` order.
3. **Per-recipient redaction:** for each intended recipient (typically `attendee_ids`, plus any
   portal-visible subset), the system determines which agenda items that recipient is NOT
   authorized to see (confidential items outside their remit) and generates a recipient-specific
   copy with those items excluded — **before** distribution, never redacted after the fact
   (BR-BOARD-003).
4. System stores the merged pack (and each redacted variant, if per-recipient copies are generated)
   in Documents (feature-flagged; `ir.attachment` fallback on Community).
5. Secretary distributes: internal notification + portal availability for Director Portal
   recipients.

## Validation
- N/A beyond the parent meeting's state (packs are typically compiled once the agenda is
  reasonably final, i.e. meeting `state` in `scheduled` or later — `[ENGINEERING DETAIL]`, not
  explicitly gated in source).

## Database changes
- `govoo.board.pack` create/update; `meeting.pack_id` set.

## Notifications
- `mail.thread` message; portal notification to Director Portal recipients that a pack is
  available.

## Documents generated
- Merged PDF (and redacted per-recipient variants, if implemented as separate documents rather than
  dynamic per-request rendering — `[ENGINEERING DETAIL]`, either approach satisfies the source
  requirement as long as redaction happens before the recipient can see the content).

## Audit events
- `mail.thread` on the pack record; distribution events (who received which variant, when) logged
  `[RECOMMENDED]`.

## Portal behavior
- Director Portal users access their redacted variant via the standard portal record-rule/token
  mechanism (`security/portal-security.md`) — never the unredacted merge.

## Failure scenarios
- If Documents (Enterprise) is unavailable, fall back to `ir.attachment` per the feature-flag
  pattern — the workflow must still complete (see AC-09).
- A redaction rule that would exclude an item for a recipient who is nonetheless an
  `attendee_ids` member must be resolved in favor of exclusion (fail closed on confidentiality) —
  `[ENGINEERING DETAIL — exact precedence rule between "invited attendee" and "authorized for this
  confidential item" not stated in source; recommend confidentiality wins].`

## Completion criteria
- Pack compiled; every recipient's variant correctly excludes unauthorized confidential items;
  pack linked to the meeting.

## Acceptance criteria
- *Given* an agenda item marked confidential and a recipient not authorized for it, *when* their
  pack is generated, *then* that item's content is excluded (FR-BOARD-003 acceptance criterion,
  also AC-01 context).
