# Integration: Surveys

Source: §3.3, §7.6 of the source spec.

- **Purpose:** Board/committee performance evaluations and quizzes, reusing Odoo's Surveys app
  rather than building a bespoke question-authoring UI (reuse-before-build).
- **Integration owner:** `govoo_evaluation` (`govoo.evaluation.campaign.survey_id`).
- **Direction:** Govoo → Surveys (create/link a survey, define participants), Surveys → Govoo (read
  `survey.user_input` responses for aggregation into `govoo.evaluation.result`).
- **Data exchanged:** survey definition (questions), participant invitations, individual responses.
- **Trigger:** campaign creation (link/create survey); campaign `state → 'open'` (send invitations);
  campaign `state → 'closed'` (aggregate results).
- **Failure behavior:** Surveys is Community-available, so no feature-flag fallback is required for
  this integration (unlike Documents/Sign/Dashboards).
- **Feature flag:** none needed (`survey` is a hard dependency of `govoo_evaluation`, not optional).
- **Community fallback:** N/A.
- **Enterprise dependency:** none.
- **Security:** individual `survey.user_input` rows tied to a `govoo.evaluation.campaign` are
  restricted per `security/record-rules.md` §6 — this is the most security-sensitive aspect of this
  integration, more so than the integration mechanics themselves.
- **Testing:** TC-EVAL-001 (aggregation correctness), TC-EVAL-002 (confidentiality — see
  `testing/security-tests.md`).
