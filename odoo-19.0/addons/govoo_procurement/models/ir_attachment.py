# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, models
from odoo.exceptions import ValidationError

_LOCKED_RES_MODELS = ('govoo.tender', 'purchase.order')


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _get_governing_tender_ids(self, extra_res_model=None, extra_res_id=None):
        """Resolve the tender(s) that govern these attachments' lock state:
        directly for a tender's own document_ids, or indirectly for a
        vendor bid's document_ids (issue #338) via its govoo_tender_id --
        a bid's documents are part of the same tender case file and lock
        on the same trigger."""
        tender_ids = set()
        bid_ids = set()
        for rec in self:
            if rec.res_model == 'govoo.tender' and rec.res_id:
                tender_ids.add(rec.res_id)
            elif rec.res_model == 'purchase.order' and rec.res_id:
                bid_ids.add(rec.res_id)
        if extra_res_model == 'govoo.tender' and extra_res_id:
            tender_ids.add(extra_res_id)
        elif extra_res_model == 'purchase.order' and extra_res_id:
            bid_ids.add(extra_res_id)
        if bid_ids:
            bids = self.env['purchase.order'].sudo().browse(bid_ids).exists()
            tender_ids.update(bids.mapped('govoo_tender_id').ids)
        return tender_ids

    def _check_tender_documents_not_locked(self, extra_res_model=None, extra_res_id=None):
        """Issue #306 follow-up, extended by #338: once a tender is
        Awarded, its documents -- and every one of its bids' own
        documents -- are the permanent record of what informed that
        decision and must not be quietly creatable/deletable afterward --
        same discipline as govoo.minutes locking content once approved, or
        govoo.contract blocking unlink() once executed. Checked here, on
        ir.attachment itself, rather than via a write() override on
        govoo.tender/purchase.order, because a file-upload widget
        creates/removes the underlying ir.attachment directly -- it does
        not necessarily round-trip through either record's own write().
        """
        tender_ids = self._get_governing_tender_ids(extra_res_model, extra_res_id)
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
            if vals.get('res_model') in _LOCKED_RES_MODELS and vals.get('res_id'):
                self._check_tender_documents_not_locked(
                    extra_res_model=vals['res_model'], extra_res_id=vals['res_id'],
                )
        return super().create(vals_list)

    def unlink(self):
        self._check_tender_documents_not_locked()
        return super().unlink()
