# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging
import os

from cryptography.fernet import Fernet, InvalidToken

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .govoo_ai_request import AI_FEATURE_SELECTION

_logger = logging.getLogger(__name__)

# govoo is sold as self-hosted-per-client SaaS (each client runs Govoo on
# their own server), not a vendor-operated shared multi-tenant instance --
# there is no central vendor infrastructure to inject a provider API key
# into every deployment. So the key genuinely has to live in this
# deployment's own database, per company. It is never stored in plaintext:
# this environment variable is a deployment-level secret (set once by
# whoever operates that client's server, never in git, never in this
# database) used only to encrypt/decrypt the api_key field below. Even a
# DBA with raw SQL access on the client's own server sees only ciphertext.
ENCRYPTION_KEY_ENV_VAR = 'GOVOO_AI_ENCRYPTION_KEY'


def _get_fernet():
    raw_key = os.environ.get(ENCRYPTION_KEY_ENV_VAR)
    if not raw_key:
        return None
    try:
        return Fernet(raw_key.encode())
    except (ValueError, TypeError):
        _logger.error('%s is set but is not a valid Fernet key.', ENCRYPTION_KEY_ENV_VAR)
        return None


class GovooAiConfig(models.Model):
    _name = 'govoo.ai.config'
    _description = 'AI Configuration'
    _inherit = ['mail.thread']

    _company_uniq = models.Constraint(
        'unique(company_id)',
        'Only one AI configuration per company.',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    active = fields.Boolean(
        string='AI Enabled',
        default=False,
        tracking=True,
        help='Master per-company switch. AI ships OFF for every company by '
             'default -- an AI Administrator must explicitly opt this '
             'company in, which requires an API key and a token cap to '
             'already be set. No govoo.ai.request can be created while '
             'this is False (see govoo_ai_request.py create()).',
    )
    provider = fields.Selection(
        selection=[('openai', 'OpenAI (direct API)')],
        string='AI Provider',
        default='openai',
        tracking=True,
        help='Confirmed as OpenAI, direct platform API (not Azure OpenAI, '
             'not self-hosted) -- docs/spec/decisions/confirmed-decisions.md '
             'entry [24]. Kept as a real Selection, not a hard-coded '
             'constant, per AI-N08 (swappable model layer): this field is '
             'the only place a consumer feature learns which provider is '
             'active, so it can move without touching any of them.',
    )
    api_key = fields.Char(
        string='API Key',
        compute='_compute_api_key',
        inverse='_inverse_api_key',
        groups='govoo_ai.group_govoo_ai_administrator',
        help="This client's own API key for the provider above. Encrypted "
             'at rest (see api_key_encrypted) -- never tracked in the '
             'chatter, never included in any AI request log, restricted to '
             'the AI Administrator group at the field level so no other '
             'role can read it even via RPC.',
    )
    api_key_encrypted = fields.Char(
        string='API Key (Encrypted)',
        groups='govoo_ai.group_govoo_ai_administrator',
        copy=False,
        readonly=True,
        help='Ciphertext only -- never rendered in any view. Decrypted on '
             'the fly by api_key when an AI Administrator opens this form; '
             'never stored decrypted anywhere.',
    )
    data_region = fields.Selection(
        selection=[],
        string='Data Region',
        tracking=True,
        help='[CONFIRM] Hosting region/residency is unresolved '
             '(open-decisions.md item 25 -- the direct OpenAI API offers no '
             'region pinning, which makes the Rwanda NCSA/Law 058/2021 '
             'question more pressing, not less). Left with no selectable '
             'options until counsel/NCSA confirm a value; do not add '
             'options here without updating decisions/confirmed-decisions.md.',
    )
    monthly_token_cap = fields.Integer(
        string='Monthly Token Cap',
        default=0,
        tracking=True,
        help='0 = no AI calls permitted. A positive value is the hard '
             'monthly ceiling enforced in govoo_ai_request.py create() -- '
             'this is also the commercial cost-control mechanism, since '
             'govoo_ai is a metered paid add-on.',
    )
    ai_f01 = fields.Boolean(string='AI-F01: Minute Drafting', tracking=True)
    ai_f04 = fields.Boolean(string='AI-F04: Board-Pack Summarization', tracking=True)
    ai_f05 = fields.Boolean(string='AI-F05: Agenda Drafting', tracking=True)
    ai_f07 = fields.Boolean(string='AI-F07: Data Extraction', tracking=True)
    ai_f08 = fields.Boolean(string='AI-F08: Semantic Search (RAG)', tracking=True)
    ai_f09 = fields.Boolean(string='AI-F09: Governance Q&A', tracking=True)
    ai_f10 = fields.Boolean(string='AI-F10: Regulatory Horizon-Scanning', tracking=True)
    ai_f11 = fields.Boolean(string='AI-F11: Deadline Risk Scoring', tracking=True)
    ai_f12 = fields.Boolean(string='AI-F12: Narrative Drafting', tracking=True)
    ai_f13 = fields.Boolean(string='AI-F13: Anomaly Detection', tracking=True)
    ai_f14 = fields.Boolean(string='AI-F14: Evaluation Analysis', tracking=True)
    ai_f15 = fields.Boolean(string='AI-F15: Director Knowledge Assistant', tracking=True)
    ai_f16 = fields.Boolean(string='AI-F16: Assisted Translation', tracking=True)

    def _compute_api_key(self):
        fernet = _get_fernet()
        for rec in self:
            if not rec.api_key_encrypted or not fernet:
                rec.api_key = False
                continue
            try:
                rec.api_key = fernet.decrypt(rec.api_key_encrypted.encode()).decode()
            except InvalidToken:
                _logger.warning(
                    'Could not decrypt the API key for govoo.ai.config %s -- '
                    '%s may have changed since it was saved.',
                    rec.id, ENCRYPTION_KEY_ENV_VAR,
                )
                rec.api_key = False

    def _inverse_api_key(self):
        fernet = _get_fernet()
        for rec in self:
            if not rec.api_key:
                rec.api_key_encrypted = False
                continue
            if not fernet:
                raise ValidationError(_(
                    'Cannot save an API key: the %s environment variable is '
                    'not configured on this server. Ask whoever manages '
                    'this deployment to set it before entering a key here.'
                ) % ENCRYPTION_KEY_ENV_VAR)
            rec.api_key_encrypted = fernet.encrypt(rec.api_key.encode()).decode()

    @api.model_create_multi
    def create(self, vals_list):
        # Not an @api.constrains: api_key's inverse (which populates the
        # actually-stored api_key_encrypted) runs after the row is
        # inserted, so a constrains check listing api_key_encrypted would
        # fire before that value exists whenever active/api_key are set
        # together on create. Checking after super().create() guarantees
        # the inverse has already run.
        records = super().create(vals_list)
        records._check_active_requires_cap_and_key()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {'active', 'monthly_token_cap', 'api_key', 'api_key_encrypted'} & set(vals):
            self._check_active_requires_cap_and_key()
        return res

    def _check_active_requires_cap_and_key(self):
        for rec in self:
            if not rec.active:
                continue
            if rec.monthly_token_cap <= 0:
                raise ValidationError(_(
                    'A monthly token cap greater than zero must be set '
                    'before enabling AI for this company -- this is a '
                    'deliberate cost-control gate, not an oversight.'
                ))
            if not rec.api_key_encrypted:
                raise ValidationError(_(
                    'An API key must be set before enabling AI for this company.'
                ))

    def is_feature_enabled(self, feature_code):
        """Single choke point every consumer feature (and this layer's own
        create() guard) must call before invoking an AI feature -- never
        re-derive this check ad hoc elsewhere."""
        self.ensure_one()
        if feature_code not in dict(AI_FEATURE_SELECTION):
            raise ValueError('Unknown AI feature code: %s' % feature_code)
        if not self.active:
            return False
        return bool(self[feature_code])
