# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, models
from odoo.exceptions import ValidationError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _check_tender_documents_not_locked(self, extra_tender_id=None):
        """Issue #306 follow-up: once a tender is Awarded, its documents are
        the permanent record of what informed that decision and must not be
        quietly creatable/deletable afterward -- same discipline as
        govoo.minutes locking content once approved, or govoo.contract
        blocking unlink() once executed. Checked here, on ir.attachment
        itself, rather than via a govoo.tender.write() override, because a
        file-upload widget creates/removes the underlying ir.attachment
        directly -- it does not necessarily round-trip through the tender
        record's own write().
        """
        tender_ids = {
            rec.res_id for rec in self
            if rec.res_model == 'govoo.tender' and rec.res_id
        }
        if extra_tender_id:
            tender_ids.add(extra_tender_id)
        if not tender_ids:
            return
        locked = self.env['govoo.tender'].sudo().browse(tender_ids).filtered(
            lambda t: t.evaluation_stage == 'awarded'
        )
        if locked:
            raise ValidationError(_(
                'Documents cannot be added or removed once a tender is '
                'Awarded — they are part of its permanent record.'
            ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('res_model') == 'govoo.tender' and vals.get('res_id'):
                self._check_tender_documents_not_locked(extra_tender_id=vals['res_id'])
        return super().create(vals_list)

    def unlink(self):
        self._check_tender_documents_not_locked()
        return super().unlink()
