# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GovooRegisterEntry(models.Model):
    """Append-only audit ledger for all statutory registers.

    No group may write() or unlink() on this model. Defence in depth:
    ir.model.access.csv already withholds write/unlink permissions, and
    these Python overrides raise UserError as a second barrier.
    """
    _name = 'govoo.register.entry'
    _description = 'Register Audit Entry'
    _order = 'effective_date desc, id desc'

    register_model = fields.Char(
        string='Register',
        required=True,
        readonly=True,
    )
    res_id = fields.Integer(
        string='Record ID',
        required=True,
        readonly=True,
    )
    change_type = fields.Selection(
        selection=[
            ('create', 'Created'),
            ('update', 'Updated'),
            ('cease', 'Ceased'),
        ],
        string='Change Type',
        required=True,
        readonly=True,
    )
    effective_date = fields.Date(
        string='Effective Date',
        required=True,
        readonly=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Changed By',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    notes = fields.Text(
        string='Notes',
        readonly=True,
    )

    # Plain labels for the free-text register_model so display_name never
    # leaks the raw technical model name (e.g. "govoo.register.director")
    # into a user-facing string, per this repo's CLAUDE.md rule.
    _REGISTER_MODEL_LABELS = {
        'govoo.register.director': 'Director',
        'govoo.register.member': 'Member',
        'govoo.register.beneficial.owner': 'Beneficial Owner',
        'govoo.register.charge': 'Charge',
    }

    @api.depends('register_model', 'change_type', 'effective_date')
    def _compute_display_name(self):
        # No plain-text field on this model, so display_name would
        # otherwise fall back to the raw "govoo.register.entry,<id>" string.
        change_type_labels = dict(self._fields['change_type']._description_selection(self.env))
        for rec in self:
            register_label = self._REGISTER_MODEL_LABELS.get(rec.register_model, _('Register'))
            change_label = change_type_labels.get(rec.change_type, rec.change_type)
            rec.display_name = _('%(register)s register — %(change)s (%(date)s)') % {
                'register': register_label,
                'change': change_label,
                'date': rec.effective_date or _('no date'),
            }

    def write(self, vals):
        raise UserError(_('Register audit entries are immutable and cannot be modified.'))

    def unlink(self):
        raise UserError(_('Register audit entries are immutable and cannot be deleted.'))

    @api.model
    def _log_entry(self, register_model, res_id, change_type, effective_date, notes=None):
        """Helper to create an audit entry. Called by register models."""
        return self.create({
            'register_model': register_model,
            'res_id': res_id,
            'change_type': change_type,
            'effective_date': effective_date,
            'company_id': self.env.company.id,
            'notes': notes,
        })
