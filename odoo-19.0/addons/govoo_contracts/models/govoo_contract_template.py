# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models


class GovooContractTemplate(models.Model):
    """Template library (FR-CM-04/FR-CM-05): reusable document templates
    with merge fields, generating a draft govoo.contract pre-populated
    with its mandatory clauses (plus any optional clauses explicitly
    selected) -- docs/spec/modules/govoo_contracts.md.
    """
    _name = 'govoo.contract.template'
    _description = 'Contract Template'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    contract_type_id = fields.Many2one(
        comodel_name='govoo.contract.type',
        string='Contract Type',
        ondelete='restrict',
    )
    body = fields.Html(
        string='Template Body',
        help='Template body with merge fields from partner/company data '
             '(CM-F04) -- rendered by the "Generated Contract Document" '
             'QWeb report on the generated govoo.contract.',
    )
    language = fields.Selection(
        selection=[
            ('en', 'English'),
            ('fr', 'French'),
            ('rw', 'Kinyarwanda'),
        ],
        string='Language',
        default='en',
        required=True,
        tracking=True,
    )
    clause_ids = fields.Many2many(
        comodel_name='govoo.contract.clause',
        string='Clauses',
        help='Every mandatory clause here is always included when '
             'generating a contract from this template; optional clauses '
             'are offered but not auto-included.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    def action_generate_contract(self, counterparty_id, extra_clause_ids=None):
        """Generate a draft govoo.contract from this template, merging
        partner/company field values -- reuses the same
        govoo.contract/QWeb-report pattern already established elsewhere
        in this codebase, not a new templating engine.

        Mandatory clauses on this template are always included; clauses
        in extra_clause_ids are included only if they belong to this
        template and are not already mandatory (optional clauses are
        never auto-included, per BR/FR-CM-04)."""
        self.ensure_one()
        mandatory_clauses = self.clause_ids.filtered('is_mandatory')
        optional_selected = self.env['govoo.contract.clause']
        if extra_clause_ids:
            optional_selected = self.clause_ids.filtered(
                lambda c: not c.is_mandatory and c.id in extra_clause_ids,
            )
        contract = self.env['govoo.contract'].create({
            'name': _('New Contract - %s') % self.name,
            'contract_type_id': self.contract_type_id.id,
            'counterparty_id': counterparty_id,
            'company_id': self.company_id.id,
            'template_id': self.id,
            'clause_ids': [(6, 0, (mandatory_clauses + optional_selected).ids)],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract'),
            'res_model': 'govoo.contract',
            'view_mode': 'form',
            'res_id': contract.id,
        }
