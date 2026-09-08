# Module: govoo_evaluation

Source: §3.2, §7.6 of the source spec. Build order: **Step 7** (depends on `govoo_base`; can run in
parallel with steps 2-6 since it does not depend on them).

## Module overview
- **Purpose:** Board performance evaluations, as a thin wrapper over standard Surveys
  (reuse-before-build).
- **Responsibility:** Evaluation campaigns and confidential result aggregation.
- **Depends on (Odoo):** `base`, `mail`, `survey`.
- **Depends on (custom):** `govoo_base`.
- **Owns:** `govoo.evaluation.campaign`, `govoo.evaluation.result`.
- **Must NOT own:** survey question authoring UI (delegated entirely to standard Surveys).

## Odoo technical structure
```
govoo_evaluation/
|-- __init__.py
|-- __manifest__.py            # depends: govoo_base, survey
|-- models/
|   |-- __init__.py
|   |-- govoo_evaluation_campaign.py
|   `-- govoo_evaluation_result.py
|-- views/
|-- security/
|   |-- ir.model.access.csv
|   `-- govoo_evaluation_security.xml   # confidentiality record rules
|-- data/
|-- report/
|   `-- (trend dashboard data source, not necessarily a QWeb report)
|-- tests/
|   |-- test_campaign.py
|   `-- test_result_confidentiality.py
`-- i18n/
```

## Models

### `govoo.evaluation.campaign`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | Yes | |
| `committee_id` | Many2one `govoo.committee` | No | |
| `survey_id` | Many2one `survey.survey` | Yes | |
| `evaluation_type` | Selection (`board`/`committee`/`peer`/`chair`/`self`) | Yes | |
| `participant_ids` | Many2many `res.partner` | No | |
| `state` | Selection (`draft`/`open`/`closed`) | Yes | default `draft` |
- **Inheritance:** `mail.thread`.
- **Constraints:** `participant_ids` should be committee members when `evaluation_type` is `board`,
  `committee`, or `peer` `[ENGINEERING DETAIL]`.
- **Access requirements:** company/committee-scoped.
- Source: §7.6.1. Requirement: FR-EVAL-001.

### `govoo.evaluation.result`
- **Description:** Aggregated scores per participant/dimension from `survey.user_input`, feeding
  trend dashboards. Confidentiality enforced by record rules.
- **Fields:** `campaign_id` (m2o), `dimension` (Char/Selection), `aggregate_score` (Float,
  computed), `participant_count` (Integer, computed) — deliberately **no** field exposing a single
  respondent's raw answer to unauthorized roles.
- **Inheritance:** `mail.thread` (aggregate-level activity only).
- **Access requirements:** raw `survey.user_input` rows tied to the campaign are restricted so that
  only Secretary/Admin (or the respondent viewing their own input) can read them; all other roles
  see only `govoo.evaluation.result` aggregates. See `security/record-rules.md`.
- Source: §7.6.2. Requirement: FR-EVAL-002. Business rule: BR-EVAL-001.

## Tests
- TC-EVAL-001: results aggregate correctly from survey inputs.
- TC-EVAL-002: individual responses are not exposed to non-authorized roles.

## Definition of Done checklist
See `implementation/module-checklists.md` — `govoo_evaluation` section.
