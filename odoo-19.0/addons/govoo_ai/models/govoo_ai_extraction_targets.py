# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

# One upload field pair and document-field onchange per AI-F07 extraction
# target (see EXTRACTION_FIELD_MAP in govoo_ai_extraction.py), added here
# via _inherit rather than editing govoo_base/govoo_secretarial/
# govoo_shares/govoo_contracts' own model files -- those modules stay
# unaware that AI features exist; govoo_ai is the one depending on them,
# never the other way. Each class only differs in which of that model's
# own document fields it targets.
#
# Issue #233: the document-field onchange is what makes extraction run
# automatically the moment a document is uploaded or selected (when
# AI-F07 is enabled) -- no "Scan Document" button needed (removed: it
# became redundant once upload itself triggers extraction). The "AI >
# Extract from Document" menu's wizard remains as the fallback for the
# disabled case, or as an explicit redo.
#
# govoo.contract is the one exception to the upload-field pattern below:
# its executed_document_upload/_filename fields and their own
# upload-handling onchange already live in govoo_contracts itself (a
# plain document-upload UX improvement, independent of AI, added before
# this feature) -- only its extraction-trigger onchange is added here.


def _upload_onchange(document_field, upload_field, filename_field):
    """Build an onchange handler that turns a direct file upload into a
    real ir.attachment and selects it as `document_field` -- identical
    in behavior to govoo_contracts' own executed_document_upload
    handler (including: never clear the upload field afterward, since
    that was the exact "looks broken, click repeatedly" bug found and
    fixed twice already on this feature). Field names are passed in
    explicitly rather than derived from `document_field` by string
    manipulation -- the two don't share a single, naively-reversible
    naming rule (e.g. `appointment_document_id` -> the upload field is
    `appointment_document_upload`, not `appointment_document_id_upload`)."""
    def _onchange(self):
        upload_value = getattr(self, upload_field)
        if upload_value:
            attachment = self.env['ir.attachment'].create({
                'name': getattr(self, filename_field) or _('Uploaded document'),
                'datas': upload_value,
            })
            setattr(self, document_field, attachment)
    return _onchange


def _extraction_onchange(document_field):
    """Build an onchange handler that runs AI-F07 extraction (when
    enabled) the moment `document_field` is set to a real attachment --
    whether that attachment just got there via a fresh upload or by
    picking an existing one from the field's own search box. A no-op,
    silent return when AI-F07 is disabled or nothing was extracted --
    the field still gets set either way; this only ever adds to that."""
    def _onchange(self):
        attachment = getattr(self, document_field)
        if not attachment:
            return None
        warning = self.env['govoo.ai.extraction'].apply_to_record(self, attachment.id)
        if warning:
            return {'warning': warning}
        return None
    return _onchange


class GovooAppointmentAiExtraction(models.Model):
    _inherit = 'govoo.appointment'

    appointment_document_upload = fields.Binary(string='Upload a File')
    appointment_document_upload_filename = fields.Char()

    _onchange_appointment_document_upload = api.onchange('appointment_document_upload')(
        _upload_onchange(
            'appointment_document_id',
            'appointment_document_upload', 'appointment_document_upload_filename',
        ),
    )
    _onchange_appointment_document_id = api.onchange('appointment_document_id')(
        _extraction_onchange('appointment_document_id'),
    )


class GovooRegisterBeneficialOwnerAiExtraction(models.Model):
    _inherit = 'govoo.register.beneficial.owner'

    evidence_document_upload = fields.Binary(string='Upload a File')
    evidence_document_upload_filename = fields.Char()

    _onchange_evidence_document_upload = api.onchange('evidence_document_upload')(
        _upload_onchange(
            'evidence_document_id',
            'evidence_document_upload', 'evidence_document_upload_filename',
        ),
    )
    _onchange_evidence_document_id = api.onchange('evidence_document_id')(
        _extraction_onchange('evidence_document_id'),
    )


class GovooRegisterChargeAiExtraction(models.Model):
    _inherit = 'govoo.register.charge'

    charge_document_upload = fields.Binary(string='Upload a File')
    charge_document_upload_filename = fields.Char()

    _onchange_charge_document_upload = api.onchange('charge_document_upload')(
        _upload_onchange(
            'charge_document_id',
            'charge_document_upload', 'charge_document_upload_filename',
        ),
    )
    _onchange_charge_document_id = api.onchange('charge_document_id')(
        _extraction_onchange('charge_document_id'),
    )


class GovooShareAllotmentAiExtraction(models.Model):
    _inherit = 'govoo.share.allotment'

    certificate_document_upload = fields.Binary(string='Upload a File')
    certificate_document_upload_filename = fields.Char()

    _onchange_certificate_document_upload = api.onchange('certificate_document_upload')(
        _upload_onchange(
            'certificate_document_id',
            'certificate_document_upload', 'certificate_document_upload_filename',
        ),
    )
    _onchange_certificate_document_id = api.onchange('certificate_document_id')(
        _extraction_onchange('certificate_document_id'),
    )


class GovooShareTransferAiExtraction(models.Model):
    _inherit = 'govoo.share.transfer'

    transfer_instrument_upload = fields.Binary(string='Upload a File')
    transfer_instrument_upload_filename = fields.Char()

    _onchange_transfer_instrument_upload = api.onchange('transfer_instrument_upload')(
        _upload_onchange(
            'transfer_instrument_id',
            'transfer_instrument_upload', 'transfer_instrument_upload_filename',
        ),
    )
    _onchange_transfer_instrument_id = api.onchange('transfer_instrument_id')(
        _extraction_onchange('transfer_instrument_id'),
    )


class GovooContractAiExtraction(models.Model):
    _inherit = 'govoo.contract'

    # executed_document_upload/_filename and their own upload-handling
    # onchange already exist in govoo_contracts/models/govoo_contract.py
    # -- only the extraction trigger is added here.
    _onchange_executed_document_id = api.onchange('executed_document_id')(
        _extraction_onchange('executed_document_id'),
    )
