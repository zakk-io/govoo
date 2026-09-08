# Business Rules

Source: derived from §3, §6, §7, §8 of the source spec. Every rule has a stable ID referenced from
`requirements/product-requirements.md`, `data-model/constraints.md`, and `testing/`.

## govoo_base

**BR-BASE-001** — PII fields on `res.partner` (`govoo_national_id`, `govoo_date_of_birth`) are
readable/writable only by Company Secretary and Board Administrator groups. Enforcement: field-level
security via a restricted view/group or `groups=` attribute on the field definition, not
UI-only hiding. *Source §6.2.*

**BR-BASE-002** — `res.company.govoo_registered_office_id` must resolve to a Rwanda address for
Rwanda-localized deployments. *Source §8.1; exact validation `[CONFIRM]`.*

**BR-BASE-003** — `govoo.appointment.state` is always computed from `date_appointed`/
`date_resigned`; it is never a directly editable field. `state = 'active'` when `date_resigned` is
unset or in the future; `state = 'resigned'` otherwise. *Source §7.1.3.*

**BR-BASE-004** — A `govoo.committee` cannot be its own ancestor via `parent_committee_id` (no
cycles); `parent_committee_id`, if set, must belong to the same `company_id`. *Engineering rule
derived from §7.1.4 to keep committee hierarchy well-formed; not stated verbatim in source.*

## Security (govoo_base, cross-cutting — source §6)

**BR-SEC-001** — Multi-company isolation: every transactional model has `company_id` with
`check_company=True`, and standard multi-company record rules apply. A corporate-services firm
administering many client entities in one database MUST NOT allow cross-entity data leakage.
*Source §6.2.*

**BR-SEC-002** — Need-to-know record rules:
- Director portal user sees only meetings/packs of committees they belong to.
- Shareholder sees only their own `govoo.share.holding` and shareholder resolutions.
- Auditor group has global read, no write, across all governance models.
*Source §6.2.*

**BR-SEC-003** — Field-level restriction: sensitive PII (national ID, date of birth) is restricted
to Secretary/Admin groups (see BR-BASE-001). *Source §6.2.*

**BR-SEC-004** — Separation of duties: Secretary/Admin **prepare** records; Directors
**approve/vote/sign**; Board Administrators **cannot cast board votes**, even though they can
configure the system. *Source §6.1, §6.2.*

**BR-SEC-005** — Audit: every transactional model inherits `mail.thread` (+
`mail.activity.mixin` where applicable); statutory fields use `tracking=True`. *Source §6.2, §9.*

**BR-SEC-006** — Portal exposure never relies on URL-guessing protection alone; every
portal-exposed record uses `portal.mixin` access tokens **combined with** the record rules in
BR-SEC-002. *Source §6.3.*

## govoo_secretarial

**BR-SEC-STAT-001** *(register-of-directors)* — The register of directors is a derived/curated view
over `govoo.appointment`; it is never independently data-entered in a way that could diverge from
appointment records. *Source §7.2.1.*

**BR-SEC-STAT-002** *(register-of-members)* — The register of members is populated from
`govoo.share.holding`; `date_ceased` is set when a partner's aggregate holding across all classes
reaches zero. *Source §7.2.2, §7.3.4.*

**BR-SEC-STAT-003** *(beneficial ownership)* — `nature_of_control` categories and their percentage
thresholds are **not** hard-coded as confirmed legal fact anywhere in the system; they are
represented as configurable/provisional data pending confirmation with a Rwandan legal advisor.
*Source §7.2.3; §13 item 4 — hard `[CONFIRM]`.*

**BR-SEC-STAT-004** *(register of charges)* — Charges are never deleted; `satisfied` is toggled
instead, preserving full history. *Source §7.2.4 (consistent with the register subsystem's
append-only philosophy).*

**BR-SEC-STAT-005** *(append-only ledger)* — `govoo.register.entry` records are write-once: no
group, including Board Administrator, may edit or delete an existing entry via ORM or UI. This is
enforced at the `ir.model.access.csv` level (no `write`/`unlink` permission for any group) and, as
defense in depth, in model `write()`/`unlink()` overrides that raise `UserError`. *Source §7.2.5.*

## govoo_shares

**BR-SHARE-001** — Cumulative `govoo.share.allotment.quantity` for a given `share_class_id` must
never exceed that class's `total_authorised`. Enforced with a SQL constraint or Python
`@api.constrains` at allotment save time. *Source §7.3.1, §7.3.2.*

**BR-SHARE-002** — A `govoo.share.transfer` cannot register a `quantity` greater than the
transferor's current `govoo.share.holding` for that class at the time of registration. *Source
§7.3.3.*

**BR-SHARE-003** — `govoo.share.holding` percentages for all holders of a given class must sum to
exactly 100% (or 0% if the class has no allotments). Holdings recompute is triggered by allotment
creation and by transfer reaching `state = 'registered'`. *Source §7.3.4 acceptance test: "holding
recomputes correctly after allotment then transfer; percentages sum to 100."*

**BR-SHARE-004** — GL posting for capital events is off by default and only enabled per a
client-confirmed accounting policy. *Source §7.3.5; §13 item 7 — `[CONFIRM]`.*

## govoo_board

**BR-BOARD-001** — A meeting's `quorum_met` is computed from confirmed attendance vs
`quorum_required`; it is never manually overridden. *Source §7.4.1.*

**BR-BOARD-002** — Meeting `state` only advances via defined transitions:
`draft → scheduled → held → minuted → closed` (see `data-model/state-machines.md`); no
state may be skipped. *Source §7.4.1, general Odoo state-machine convention applied to the source's
listed states.*

**BR-BOARD-003** — Confidential agenda items are redacted from a recipient's board pack **before**
distribution if that recipient is not authorized for the item; redaction is never retroactive.
*Source §7.4.3.*

**BR-BOARD-004** — `govoo.minutes.retention_until` is computed from `govoo_rw`'s retention
configuration (10 years for minutes/resolutions), never a literal value inside `govoo_board`.
*Source §8.2.*

**BR-BOARD-005** — A resolution is only `passed` when both quorum is met **and** the majority
threshold appropriate to its `resolution_type` (ordinary/special/written) is satisfied by the
tallied, non-excluded votes. Thresholds themselves (e.g. what counts as "special majority") follow
the client's articles of association and applicable law and are configuration, not a hard-coded
percentage `[CONFIRM per company articles / Rwandan law]`. *Source §7.4.5, §7.4.6.*

**BR-BOARD-006** — Vote `weight` is 1.0 per director for board/committee resolutions; for
shareholder resolutions, `weight` is sourced from the voter's `govoo.share.holding.voting_power` at
the time of voting. *Source §7.4.6.*

**BR-BOARD-007** — A vote with `is_conflicted = True` (declared interest) is excluded from the
tally where the applicable governance rule requires it. *Source §7.4.6.*

**BR-BOARD-008** — E-signature and electronic/written-resolution validity is gated: Sign integration
and e-voting-as-legally-binding features must not be presented as legally conclusive until Rwandan
legal validity is confirmed for the client's articles. *Source §7.4.6 `[CONFIRM]`; §13 item 3.*

## govoo_compliance

**BR-COMP-001** — Obligation templates seeded from `govoo_rw` (or any source) as provisional are
`active = False` until a human confirms them; unverified deadlines are never presented as
authoritative. *Source §7.5.3 `[IMPORTANT]`; §8.2.*

**BR-COMP-002** — `govoo.compliance.instance.due_date` is computed per the obligation's `basis`
(fixed_date / fye_relative / event_relative) from confirmed configuration data only — never a
hard-coded date in Python. *Source §7.5.1, §7.5.2, §9.*

**BR-COMP-003** — An instance whose `due_date` has passed and whose `state` is not `filed` or
`waived` transitions to `late` and triggers escalation. *Source §7.5.3.*

**BR-COMP-004** — Filing-pack export produces documents for manual submission; it never assumes an
automated government filing API exists unless/until one is confirmed. *Source §7.5.4; §13 item 6.*

## govoo_rw

**BR-RW-001** — Currency is configured as RWF with 0 decimal places system-wide for Rwanda
deployments; all `Monetary` fields must respect this (no code assumes 2-decimal formatting).
*Source §8.1, §9.*

**BR-RW-002** — No tax rate, statutory date, threshold, or legal article number is ever hard-coded
as a Python literal anywhere in the system; all such values are data records, and any value not
yet confirmed by a licensed Rwandan advocate/tax advisor defaults to inactive/disabled and is
labelled provisional wherever shown. *Source §8.2, §8.3, §9, and the source document's closing
disclaimer.*

**BR-RW-003** — The retention/disposal engine reconciles the 10-year statutory retention against
data-subject erasure rights before deleting any record; it does not delete solely because a
retention period has technically elapsed if a legal hold or open erasure request applies.
*Source §10.3 `[CONFIRM exact reconciliation process]`.*

## govoo_evaluation

**BR-EVAL-001** — Individual `survey.user_input` responses tied to a `govoo.evaluation.campaign`
are never exposed to a participant other than Secretary/Admin (or the respondent viewing their own
input); only aggregated `govoo.evaluation.result` scores are visible to the broader authorized
audience. *Source §7.6.2.*

## Non-functional / cross-cutting (source §10)

**BR-NFR-001** — Real personal data, including backups, is hosted only in Rwanda or an
NCSA-authorized location; build/staging environments use only synthetic/anonymized data unless
hosted under the same constraint. *Source §10.1 `[CONFIRM exact wording/process with NCSA/counsel]`.*

**BR-NFR-002** — A backup is considered valid only if a restore from it has been tested; RPO/RTO
targets are `[CONFIRM]` per tier. *Source §10.4.*

**BR-NFR-003** — Identity/CDD data is captured on directors, shareholders, and beneficial owners at
onboarding. *Source §10.5.*
