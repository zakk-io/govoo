# Integration: Sign (e-signature)

Source: §3.3, §7.3.3 (transfer instrument signing), §7.4.4 (minutes signing), §7.4.5/§7.4.6
(resolution signing), §13 item 3 (`[CONFIRM]` legal validity).

- **Purpose:** E-signature workflow for transfer instruments, minutes, and resolutions.
- **Integration owner:** `govoo_shares` (`govoo.share.transfer.sign_request_id`), `govoo_board`
  (`govoo.minutes.sign_request_id`, `govoo.resolution.sign_request_id`), `govoo_contracts`
  (`govoo.contract.sign_request_id`, addendum CM-F10).
- **Direction:** Govoo → Sign (create signature request), Sign → Govoo (webhook/poll for completion,
  store signed document).
- **Data exchanged:** document to be signed, signatory list, completion status, signed PDF.
- **Trigger:** transfer reaching `approved`; minutes reaching `approved` (if signing is part of the
  flow); resolution requiring an executed/signed record; contract reaching `approved` (moving it to
  `executed`, BR-CM-005).
- **Failure behavior:** **this integration is gated behind a legal-validity confirmation
  (`[CONFIRM]`, source §13 item 3) that is independent of the Enterprise/Community feature flag** —
  even where Sign (or its OCA equivalent) is installed, the "sign electronically" path must remain
  disabled/hidden until Rwandan legal validity of e-signature and electronic/written resolutions is
  confirmed for the client's articles of association (BR-BOARD-008). Until then, every workflow
  that would otherwise use Sign instead uses a manual "upload the signed copy" path, and the system
  must not present an e-signed record as legally conclusive. `govoo_contracts` reuses this exact
  same gate rather than a separate contract-specific legal-validity flag (BR-CM-005) — the addendum
  raises contract e-signature validity as its own open item (§9 item 3), but it is one instance of
  the same underlying confirmation, tracked as a single `decisions/open-decisions.md` item.
- **Feature flag:** two independent flags — (1) is Sign/`sign_oca` installed (technical
  availability), (2) is e-signature legally confirmed for this client (business/legal gate,
  `[CONFIRM]`). **Both** must be true before the Sign UI path is offered.
- **Community fallback:** OCA `sign_oca`, or (if legal validity remains unconfirmed regardless of
  technical availability) the manual signed-copy-upload path.
- **Enterprise dependency:** Sign app.
- **Security:** signed documents inherit the same access restrictions as their parent record
  (transfer, minutes, resolution); signature request credentials/webhooks handled per
  `security/privacy.md` §5 secrets guidance.
- **Testing:** a test proving the Sign UI path is unavailable/hidden when the legal-validity flag is
  unconfirmed, in addition to standard integration tests once confirmed.
