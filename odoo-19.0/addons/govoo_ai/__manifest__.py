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
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['govoo_base', 'muk_mcp'],
    'external_dependencies': {
        'python': ['cryptography', 'requests'],
    },
    'data': [
        'security/govoo_ai_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/govoo_ai_config_views.xml',
        'views/govoo_ai_request_views.xml',
        'views/govoo_ai_suggestion_views.xml',
        'views/govoo_ai_search_wizard_views.xml',
        'views/govoo_ai_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
