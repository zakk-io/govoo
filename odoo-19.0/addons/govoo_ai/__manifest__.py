# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo AI',
    'summary': 'Shared AI service layer: audit log, human-review queue, per-tenant config and guardrails',
    'description': """
AI Services Layer for Govoo (addendum module, issue #215 -- foundation of the
`govoo_ai` epic, issue #214):

A model-agnostic service layer other govoo_ai feature clusters (search, Q&A,
drafting, extraction, etc. -- see issue #214) call through, rather than a
feature in itself. No consumer feature may call a model provider directly.

Ships every company with AI OFF by default (`govoo.ai.config.active =
False`, `monthly_token_cap = 0`). Every AI call is logged (`govoo.ai.request`)
before and after it runs, and every AI output lands as a `govoo.ai.suggestion`
a named human must explicitly accept before it becomes part of any real
record -- never auto-committed.

Provider is OpenAI (direct API) per `docs/spec/decisions/confirmed-decisions.md`
entry [24]. Hosting region/residency, DPA/zero-retention terms and
token-cap/pricing metering remain open decisions (`open-decisions.md` items
24/25/29) -- `data_region` ships unconfigured until those are resolved;
this module only implements the mechanism.

Deployment model: govoo is sold as self-hosted-per-client SaaS (each client
runs their own Odoo instance on their own server), not a vendor-operated
shared multi-tenant service -- so each deployment's govoo.ai.config holds
that client's own API key, per company. The key is never stored in
plaintext: `api_key` is encrypted at rest with `cryptography.fernet` using
a deployment-level encryption key (the `GOVOO_AI_ENCRYPTION_KEY`
environment variable, set once by whoever operates that server -- never in
git, never in this database). Restricted to the AI Administrator group at
the field level.

AI-F08 (Semantic Search, issue #216): a bounded OpenAI tool-calling loop
grounded in this Odoo's own data via muk_mcp's existing, permission-aware
read tools (search_read/read_records/search_count/read_group/
describe_model/list_models) -- muk_mcp's write tools are never reachable
from this loop. Every claimed match is re-checked for read access before a
suggestion is created for it; the model's own output is never trusted as
proof of access.

AI-F09 (Governance Q&A, issue #217): a conversational narrative-answer loop
built on the same grounding bridge as AI-F08, adding mandatory citations and
an explicit "not found" path (never a fabricated answer). Entry point is a
persistent floating chat widget (OWL), visible only to users in the AI User
group and on the backend webclient only (never the public website layout).

AI-F07 (Data Extraction, issues #218 + #198): a single-shot OpenAI vision
call -- not a tool-calling loop, there is nothing to retrieve, only a
document to read -- that extracts a hard-allowlisted set of fields from an
uploaded scanned/executed document (a board appointment letter, a share
certificate, a charge instrument, an executed contract) into a
govoo.ai.suggestion a named human must review, correct, and explicitly
apply before any real register/cap-table/contract record is created or
updated -- never auto-committed. Depends on govoo_secretarial, govoo_shares
and govoo_contracts, since (unlike AI-F08/AI-F09's generic introspection)
this feature needs compile-time knowledge of exact field names on those
modules' specific models.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.2',
    'license': 'LGPL-3',
    'depends': ['govoo_base', 'govoo_secretarial', 'govoo_shares', 'govoo_contracts', 'muk_mcp'],
    'external_dependencies': {
        'python': ['cryptography', 'requests', 'fitz'],
    },
    'data': [
        'security/govoo_ai_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/govoo_ai_config_views.xml',
        'views/govoo_ai_request_views.xml',
        'views/govoo_ai_suggestion_views.xml',
        'views/govoo_ai_search_wizard_views.xml',
        'views/govoo_ai_extraction_wizard_views.xml',
        'views/govoo_ai_extraction_buttons.xml',
        'views/govoo_ai_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'govoo_ai/static/src/ai_chat_widget/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
