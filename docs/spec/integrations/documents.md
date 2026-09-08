# Integration: Documents

Source: §3.3, §7.4.3 (board packs), throughout §7 wherever a `*_document_id` field is listed.

- **Purpose:** Central, versioned file storage for statutory documents, board packs, certificates,
  and evidence documents.
- **Integration owner:** every module with a `*_document_id`/`document_ids` field —
  `govoo_secretarial` (evidence/charge documents), `govoo_shares` (certificates, transfer
  instruments), `govoo_board` (agenda documents, board packs, minutes, signed documents),
  `govoo_compliance` (filing documents).
- **Direction:** Govoo → Documents (store), Documents → Govoo (retrieve for viewing/merging into
  reports).
- **Data exchanged:** binary file content + metadata (filename, linked record).
- **Trigger:** any workflow step that attaches or generates a document (allotment certificate,
  board pack compile, minutes signing, filing-pack export, etc.).
- **Failure behavior:** if the Documents app (Enterprise) is not installed, every `*_document_id`
  field and document-producing action falls back to `ir.attachment` transparently — the workflow
  must still complete (AC-09). No user-facing error should occur solely because Documents is
  absent.
- **Feature flag:** `[ENGINEERING DETAIL]` check
  `env['ir.module.module'].sudo().search([('name','=','documents'),('state','=','installed')])`
  (or an equivalent cached helper) at the point of use; branch to the `ir.attachment` path if not
  installed.
- **Community fallback:** `ir.attachment`, linked via the same `*_document_id`-shaped field but
  pointing at `ir.attachment` instead of `documents.document` — `[ENGINEERING DETAIL]` this may
  require a thin abstraction (e.g. a computed/related field or a small wrapper model) so the rest
  of each module's code doesn't need two branches everywhere; document the chosen abstraction in
  code comments.
- **Enterprise dependency:** Documents app (or OCA `dms` as an alternative Community-compatible
  document management module, per `architecture/module-architecture.md` §2).
- **Security:** documents inherit the access restrictions of their linked record (e.g. a
  beneficial-ownership evidence document is at least as restricted as the
  `govoo.register.beneficial.owner` record it's attached to) — never more permissive.
- **Testing:** TC-BASE-005 (graceful degradation on Community, per AC-09).
