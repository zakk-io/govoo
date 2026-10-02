# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import models

# One tiny "Scan Document" button method per AI-F07 extraction target
# (see EXTRACTION_FIELD_MAP in govoo_ai_extraction.py), added here via
# _inherit rather than editing govoo_base/govoo_secretarial/govoo_shares/
# govoo_contracts' own model files -- those modules stay unaware that AI
# features exist; govoo_ai is the one depending on them, never the other
# way. Each method only differs in which of that model's own document
# fields to pre-fill as the wizard's attachment.


class GovooAppointmentAiExtraction(models.Model):
    _inherit = 'govoo.appointment'

    def action_open_ai_extraction_wizard(self):
        self.ensure_one()
        return self.env['govoo.ai.extraction.wizard']._open_for(
            self._name, self.id, self.appointment_document_id.id,
        )


class GovooRegisterBeneficialOwnerAiExtraction(models.Model):
    _inherit = 'govoo.register.beneficial.owner'

    def action_open_ai_extraction_wizard(self):
        self.ensure_one()
        return self.env['govoo.ai.extraction.wizard']._open_for(
            self._name, self.id, self.evidence_document_id.id,
        )


class GovooRegisterChargeAiExtraction(models.Model):
    _inherit = 'govoo.register.charge'

    def action_open_ai_extraction_wizard(self):
        self.ensure_one()
        return self.env['govoo.ai.extraction.wizard']._open_for(
            self._name, self.id, self.charge_document_id.id,
        )


class GovooShareAllotmentAiExtraction(models.Model):
    _inherit = 'govoo.share.allotment'

    def action_open_ai_extraction_wizard(self):
        self.ensure_one()
        return self.env['govoo.ai.extraction.wizard']._open_for(
            self._name, self.id, self.certificate_document_id.id,
        )


class GovooShareTransferAiExtraction(models.Model):
    _inherit = 'govoo.share.transfer'

    def action_open_ai_extraction_wizard(self):
        self.ensure_one()
        return self.env['govoo.ai.extraction.wizard']._open_for(
            self._name, self.id, self.transfer_instrument_id.id,
        )


class GovooContractAiExtraction(models.Model):
    _inherit = 'govoo.contract'

    def action_open_ai_extraction_wizard(self):
        self.ensure_one()
        return self.env['govoo.ai.extraction.wizard']._open_for(
            self._name, self.id, self.executed_document_id.id,
        )
