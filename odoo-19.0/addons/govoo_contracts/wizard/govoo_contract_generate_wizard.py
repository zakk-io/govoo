# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class GovooContractGenerateWizard(models.TransientModel):
    """Minimal UI in front of govoo.contract.template.action_generate_contract()
    -- picks the counterparty and which optional clauses to include;
    mandatory clauses are never offered as a choice."""
    _name = 'govoo.contract.generate.wizard'
    _description = 'Generate Contract from Template'

    template_id = fields.Many2one(
        comodel_name='govoo.contract.template',
        string='Template',
        required=True,
    )
    counterparty_id = fields.Many2one(
        comodel_name='res.partner',
        string='Counterparty',
        required=True,
    )
    optional_clause_ids = fields.Many2many(
        comodel_name='govoo.contract.clause',
        string='Optional Clauses',
    )

    @api.onchange('template_id')
    def _onchange_template_id(self):
        for wizard in self:
            wizard.optional_clause_ids = False

    def action_generate(self):
        self.ensure_one()
        return self.template_id.action_generate_contract(
            self.counterparty_id.id,
            self.optional_clause_ids.ids,
        )
