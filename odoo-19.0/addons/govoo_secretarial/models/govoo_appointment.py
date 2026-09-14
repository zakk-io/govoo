# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class GovooAppointment(models.Model):
    """Extends govoo.appointment (govoo_base) to keep govoo.register.director
    -- a curated view over appointments -- in sync. Lives here rather than
    in govoo_base since govoo_secretarial already depends on govoo_base,
    not the reverse.
    """
    _inherit = 'govoo.appointment'

    # Statutory Register of Directors: directors + company secretary, per
    # company-law convention -- not every committee_member appointment
    # (e.g. a sub-committee seat) belongs on this specific register.
    _REGISTER_DIRECTOR_ROLES = ('director', 'chair', 'md', 'secretary')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.role in self._REGISTER_DIRECTOR_ROLES:
                self.env['govoo.register.director'].create({
                    'appointment_id': rec.id,
                })
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'date_resigned' in vals:
            for rec in self:
                register = self.env['govoo.register.director'].search([
                    ('appointment_id', '=', rec.id),
                ], limit=1)
                if register:
                    # related fields recompute via an internal ORM path that
                    # does not invoke govoo.register.director's own write()
                    # override, so log the ledger entry directly here.
                    register._audit_log(
                        'cease' if rec.date_resigned else 'update',
                        rec.date_resigned or fields.Date.context_today(rec),
                    )
        return res
