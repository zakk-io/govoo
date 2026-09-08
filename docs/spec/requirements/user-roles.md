# User Roles / Personas

Source: §6.1 of the source spec (security groups), cross-referenced with actors named throughout
§7. See `security/access-control.md` for the full permission matrix.

## 1. Internal roles

### Governance User — `govoo_base.group_govoo_user`
- **Who:** Any internal staff member needing baseline read access to their company's governance
  data (e.g. an executive assistant, a junior compliance officer).
- **Capabilities:** Read own-company governance data. No PII fields. No create/write on statutory
  records by default.
- **Cannot:** See other companies' data; edit registers; vote; see PII.

### Company Secretary — `govoo_base.group_govoo_secretary`
- **Who:** The person legally/operationally responsible for statutory compliance, registers,
  meetings administration.
- **Capabilities:** Power user — create/manage all governance records: appointments, committees,
  registers, share transactions, meetings, agendas, packs, minutes (draft), resolutions (draft/
  open), compliance instances, filing-pack export. Full PII access.
- **Cannot:** Cast board votes on behalf of directors/shareholders (separation of duties, BR-SEC-004).

### Board Administrator — `govoo_base.group_govoo_admin`
- **Who:** IT/platform administrator responsible for configuration, users, and groups.
- **Capabilities:** System configuration, user/group management, obligation-catalogue
  configuration, module/feature-flag settings.
- **Cannot:** Cast board votes (BR-SEC-004) — configuration privilege is explicitly separated from
  governance decision-making.

### Auditor (read-only) — `govoo_base.group_govoo_auditor`
- **Who:** Internal or external auditor reviewing governance/compliance records.
- **Capabilities:** Global read access across governance models (within their assigned companies,
  per multi-company rules) — no write, anywhere.
- **Cannot:** Create, edit, or delete any record.

## 2. External (portal) roles

### Director (Portal) — `govoo_base.group_govoo_director_portal`
- **Who:** An external, non-employee board/committee director.
- **Capabilities:** View meetings, board packs, minutes, and resolutions **for committees they
  belong to only**; cast votes on resolutions they are eligible for; view their own appointment
  particulars.
- **Cannot:** See other committees' data; see other directors'/shareholders' PII; edit statutory
  registers; access via internal backend UI (portal only, no internal license).

### Shareholder (Portal) — `govoo_base.group_govoo_shareholder_portal`
- **Who:** An external shareholder.
- **Capabilities:** View their own `govoo.share.holding` (cap-table position); view and vote on
  shareholder-type resolutions they are eligible for.
- **Cannot:** See other shareholders' holdings; see board/committee (director-only) meeting data;
  edit statutory registers.

## 3. Role-to-workflow map (which roles act in which workflow)
| Workflow | Primary actor(s) | Approving/voting actor(s) | Read-only observers |
| --- | --- | --- | --- |
| Appointments | Company Secretary | — | Governance User, Auditor |
| Committees | Company Secretary, Board Administrator | — | Governance User, Director Portal (own) |
| Statutory registers | Company Secretary | — | Auditor, relevant portal user (own record) |
| Cap table (allotment/transfer) | Company Secretary | — | Auditor, Shareholder Portal (own) |
| Meetings | Company Secretary | Attendees (attendance) | Director Portal (own committee) |
| Board pack | Company Secretary | — | Director Portal (own committee, redacted) |
| Minutes | Company Secretary (draft) | Directors (approve/sign) | Auditor |
| Resolutions & voting | Company Secretary (draft/open) | Eligible directors/shareholders | Board Administrator (cannot vote) |
| Compliance obligations/instances | Company Secretary, responsible user | — | Board Administrator |
| Evaluations | Company Secretary, Board Administrator | Participants (respond) | — (results are confidential/aggregate) |

## 4. Persona notes for UI design (`ui/`)
- Internal roles (Secretary, Admin, Auditor) use the standard Odoo backend — menus/views filtered by
  group per `security/access-control.md`.
- Portal roles use `portal.mixin`-based controllers and simplified, read-mostly views — see
  `ui/portal-ui.md`.
- No role is ever shown a UI affordance (button, menu) for an action their group cannot perform;
  hiding the affordance is a UX convenience, **not** a substitute for the underlying access-rule
  enforcement (BR-SEC-006).
