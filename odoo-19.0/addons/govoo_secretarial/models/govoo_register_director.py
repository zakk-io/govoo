# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class GovooRegisterDirector(models.Model):
    """Curated view over govoo.appointment for the Register of Directors."""
    _name = 'govoo.register.director'
    _description = 'Register of Directors'
    _inherit = ['mail.thread']
    _order = 'date_appointed desc'

    appointment_id = fields.Many2one(
        comodel_name='govoo.appointment',
        string='Appointment',
        required=True,
        ondelete='restrict',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Director',
        related='appointment_id.partner_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='appointment_id.company_id',
        store=True,
        readonly=True,
    )
    role = fields.Selection(
        related='appointment_id.role',
        store=True,
        readonly=True,
    )
    date_appointed = fields.Date(
        related='appointment_id.date_appointed',
        store=True,
        readonly=True,
    )
    date_resigned = fields.Date(
        related='appointment_id.date_resigned',
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        related='appointment_id.state',
        store=True,
        readonly=True,
    )
    # [CONFIRM] exact statutory particulars required on printed extract (FR-SEC-001)
    # Additional fields TBD by legal advisor

    def _audit_log(self, change_type, effective_date):
        self.env['govoo.register.entry']._log_entry(
            register_model='govoo.register.director',
            res_id=self.id,
            change_type=change_type,
            effective_date=effective_date,
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._audit_log('create', rec.date_appointed or fields.Date.context_today(rec))
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'date_resigned' in vals:
            for rec in self:
                if rec.date_resigned:
                    rec._audit_log('cease', rec.date_resigned)
                else:
                    rec._audit_log('update', fields.Date.context_today(rec))
        return res
