# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class GovooTender(models.Model):
    _inherit = 'govoo.tender'

    contract_ids = fields.One2many(
        comodel_name='govoo.contract',
        inverse_name='tender_id',
        string='Contracts',
    )
    contract_count = fields.Integer(
        string='Contracts',
        compute='_compute_contract_count',
    )

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        """Live check: most tender viewers (Officer, Evaluator, Approver)
        hold no ACL on govoo.contract at all -- reading contract_ids
        directly here raised a hard AccessError that broke the entire
        Tenders list for them, not just this one stat button. Counting
        via a sudo()'d search_count avoids touching contract_ids (and
        its own access check) from this compute entirely; the stat
        button itself is further restricted to the groups that can
        actually open what it links to, in the view."""
        counts = self.env['govoo.contract'].sudo()._read_group(
            [('tender_id', 'in', self.ids)], ['tender_id'], ['__count'],
        )
        count_by_tender = {tender.id: count for tender, count in counts}
        for rec in self:
            rec.contract_count = count_by_tender.get(rec.id, 0)

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contracts'),
            'res_model': 'govoo.contract',
            'view_mode': 'list,form',
            'domain': [('tender_id', '=', self.id)],
            'context': {'default_tender_id': self.id},
        }
