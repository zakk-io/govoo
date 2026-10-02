# Part of Govoo. See LICENSE file for full copyright and licensing details.

import base64
import json
import logging

import odoo.modules.module
from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

# A cost/latency bound on how much of one document is sent per extraction
# call -- same engineering-constant discipline as
# govoo.ai.grounding.DEFAULT_MAX_TOOL_LOOPS, not a legal value. Almost
# every statutory document this targets (an appointment letter, a share
# certificate, a charge instrument, an executed contract's signature page)
# fits comfortably within the first few pages.
MAX_EXTRACTION_PAGES = 5

# AI-F07's hard allowlist of extraction targets (same discipline as AI-F08's
# WHITELISTED_TOOLS): extraction can never write to an arbitrary model, only
# one of these, with only these exact fields. Built from each model's real
# field definitions (see issue #218/#198 research), not guessed:
#
# - govoo.register.director is deliberately NOT a target: its rows are
#   auto-synced from govoo.appointment (see govoo_secretarial's create/write
#   overrides), so this targets govoo.appointment instead.
# - govoo.register.member and govoo.share.holding are deliberately excluded:
#   both are derived/computed from other records (share holdings and
#   allotments/transfers respectively), not manually created, and neither
#   has a document-attachment field.
# - govoo.share.class is deliberately excluded: a category/configuration
#   record, not document-backed.
# - govoo.contract only lists its date fields (not name/contract_type_id/
#   counterparty_id): contract creation already has its own
#   template-based wizard (govoo_contract_generate_wizard.py) that this
#   feature does not replace -- in practice this target is always used via
#   the smart button on an existing contract (target_res_id set), writing
#   just the extracted dates onto it.
EXTRACTION_FIELD_MAP = {
    'govoo.appointment': [
        {'name': 'partner_id', 'label': 'Person', 'type': 'many2one',
         'relation': 'res.partner', 'required': True},
        {'name': 'role', 'label': 'Role', 'type': 'selection', 'required': True,
         'selection': [
             ('director', 'Director'), ('secretary', 'Company Secretary'),
             ('chair', 'Chairperson'), ('md', 'Managing Director'),
             ('committee_member', 'Committee Member'),
         ]},
        {'name': 'date_appointed', 'label': 'Date Appointed', 'type': 'date', 'required': True},
        {'name': 'date_resigned', 'label': 'Date Resigned', 'type': 'date', 'required': False},
    ],
    'govoo.register.beneficial.owner': [
        {'name': 'partner_id', 'label': 'Beneficial Owner', 'type': 'many2one',
         'relation': 'res.partner', 'required': True},
        {'name': 'nature_of_control', 'label': 'Nature of Control', 'type': 'selection', 'required': True,
         'selection': [
             ('shares_25', 'Ownership of more than 25% of shares'),
             ('voting_25', 'Entitlement to more than 25% of voting rights'),
             ('board_appoint', 'Right to appoint majority of board members'),
             ('significant', 'Significant influence or control'),
         ]},
        {'name': 'date_became_registrable', 'label': 'Date Became Registrable', 'type': 'date', 'required': False},
    ],
    'govoo.register.charge': [
        {'name': 'chargee_partner_id', 'label': 'Chargee', 'type': 'many2one',
         'relation': 'res.partner', 'required': False},
        {'name': 'amount', 'label': 'Amount', 'type': 'monetary', 'required': False},
        {'name': 'date_created', 'label': 'Date Created', 'type': 'date', 'required': False},
        {'name': 'date_registered', 'label': 'Date Registered', 'type': 'date', 'required': False},
        {'name': 'property_description', 'label': 'Property Description', 'type': 'char', 'required': False},
    ],
    'govoo.share.allotment': [
        {'name': 'share_class_id', 'label': 'Share Class', 'type': 'many2one',
         'relation': 'govoo.share.class', 'required': True},
        {'name': 'partner_id', 'label': 'Allottee', 'type': 'many2one',
         'relation': 'res.partner', 'required': True},
        {'name': 'quantity', 'label': 'Number of Shares', 'type': 'integer', 'required': True},
        {'name': 'price_per_share', 'label': 'Price per Share', 'type': 'monetary', 'required': False},
        {'name': 'date_allotted', 'label': 'Date Allotted', 'type': 'date', 'required': False},
        {'name': 'certificate_no', 'label': 'Certificate Number', 'type': 'char', 'required': False},
    ],
    'govoo.share.transfer': [
        {'name': 'share_class_id', 'label': 'Share Class', 'type': 'many2one',
         'relation': 'govoo.share.class', 'required': True},
        {'name': 'transferor_id', 'label': 'Transferor (Seller)', 'type': 'many2one',
         'relation': 'res.partner', 'required': True},
        {'name': 'transferee_id', 'label': 'Transferee (Buyer)', 'type': 'many2one',
         'relation': 'res.partner', 'required': True},
        {'name': 'quantity', 'label': 'Number of Shares', 'type': 'integer', 'required': True},
        {'name': 'price', 'label': 'Price', 'type': 'monetary', 'required': False},
        {'name': 'date_transferred', 'label': 'Date Transferred', 'type': 'date', 'required': False},
        {'name': 'stamp_duty', 'label': 'Stamp Duty', 'type': 'monetary', 'required': False},
    ],
    'govoo.contract': [
        {'name': 'date_start', 'label': 'Start Date', 'type': 'date', 'required': False},
        {'name': 'date_end', 'label': 'End Date', 'type': 'date', 'required': False},
        {'name': 'renewal_type', 'label': 'Renewal Type', 'type': 'selection', 'required': False,
         'selection': [('fixed', 'Fixed Term'), ('auto', 'Evergreen (Auto-Renew)')]},
        {'name': 'renewal_date', 'label': 'Renewal Date', 'type': 'date', 'required': False},
    ],
}

# Human-friendly labels for EXTRACTION_FIELD_MAP's technical model names,
# shown in the wizard's "Extract Into" dropdown instead of a raw name like
# "govoo.register.beneficial.owner" -- someone new to Odoo has no reason
# to already know these technical names.
EXTRACTION_TARGET_LABELS = {
    'govoo.appointment': 'Director / Officer Appointment',
    'govoo.register.beneficial.owner': 'Register of Beneficial Owners',
    'govoo.register.charge': 'Register of Charges',
    'govoo.share.allotment': 'Share Allotment',
    'govoo.share.transfer': 'Share Transfer',
    'govoo.contract': 'Contract (Dates Only)',
}


class GovooAiExtraction(models.AbstractModel):
    """AI-F07 orchestration: OCR/vision extraction of statutory-register,
    cap-table, and contract-date fields from an uploaded scanned/executed
    document (issues #218 + #198 -- one shared pipeline, see the combined
    PR description for why).

    Unlike AI-F08/AI-F09, this is a single vision call, not a tool-calling
    loop -- there is nothing to retrieve, only a document to read -- so it
    calls govoo.ai.openai.client directly with OpenAI's native vision
    message content, which that client already passes through unmodified.
    """

    _name = 'govoo.ai.extraction'
    _description = 'AI-F07 Data Extraction Orchestration'

    def run(self, target_model, attachment_id, target_res_id=False):
        """Extract EXTRACTION_FIELD_MAP[target_model]'s fields from
        ``attachment_id`` and return the resulting govoo.ai.suggestion.

        ``target_res_id`` is optional: leave it 0/False to propose a
        brand-new record (the common case for the register/cap-table
        models), or pass an existing record's id when extracting onto a
        record the user is already editing (the common case for
        govoo.contract, whose own required fields -- name, type,
        counterparty -- are unrelated to what this extracts). Either way
        nothing is written to the target model here -- creating or
        updating the real record from an accepted suggestion is the
        wizard's job, after a human reviews every proposed value
        (AI-N02/AI-N03).

        :raise UserError: if ``target_model`` is not a supported
            extraction target, AI-F07 is not enabled for this company, the
            attachment does not exist or is not readable by the current
            user, or the document type is unsupported.
        """
        if target_model not in EXTRACTION_FIELD_MAP:
            raise UserError(_('"%s" is not a supported AI extraction target.') % target_model)
        config = self.env['govoo.ai.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        if not config or not config.is_feature_enabled('ai_f07'):
            raise UserError(_(
                'Data Extraction is not enabled for this company. An AI '
                'Administrator must enable AI and tick "AI-F07: Data '
                'Extraction" in AI > Configuration first.'
            ))
        attachment = self.env['ir.attachment'].browse(attachment_id)
        if not attachment.exists():
            raise UserError(_('The selected document could not be found.'))
        try:
            # AI-N02: a user must already be able to read the document
            # they're asking the AI to read -- the model's own output is
            # never the access check.
            attachment.check_access('read')
        except AccessError:
            raise UserError(_('You do not have access to the selected document.'))
        images, image_mimetype = self._attachment_to_images(attachment)
        messages = [
            {'role': 'system', 'content': self._build_system_prompt(target_model)},
            {'role': 'user', 'content': [
                {'type': 'text', 'text': _(
                    'Extract the fields described above from this document.'
                )},
            ] + [
                {'type': 'image_url', 'image_url': {
                    'url': 'data:%s;base64,%s' % (image_mimetype, image_b64),
                }}
                for image_b64 in images
            ]},
        ]
        request = self.env['govoo.ai.request'].create({
            'feature': 'ai_f07',
            'input_ref': 'ir.attachment,%s' % attachment_id,
            'input_summary': (_('Extract %(model)s fields from %(doc)s') % {
                'model': target_model, 'doc': attachment.name or attachment_id,
            })[:500],
        })
        try:
            response = self.env['govoo.ai.openai.client'].chat_completion(
                api_key=config.sudo().api_key,
                messages=messages,
                response_format={'type': 'json_object'},
            )
        except Exception:
            request.write({'status': 'failed'})
            # See govoo_ai_search.py::run() for why this commit is needed
            # and why it's skipped under the test harness.
            if not odoo.modules.module.current_test:
                self.env.cr.commit()
            raise
        model_name = 'openai:%s' % response.get('model', '')
        token_usage = (response.get('usage') or {}).get('total_tokens', 0)
        content = response['choices'][0]['message'].get('content')
        extracted = self._parse_extracted(target_model, content)
        suggestion = self.env['govoo.ai.suggestion'].create({
            'request_id': request.id,
            'target_model': target_model,
            'target_res_id': target_res_id or False,
            'extracted_values': json.dumps(extracted),
            'content': _('Extracted %(count)s field(s) from %(doc)s') % {
                'count': len(extracted), 'doc': attachment.name or _('the uploaded document'),
            },
            'citations': 'ir.attachment,%s' % attachment_id,
        })
        request.write({
            'status': 'done',
            'model_name': model_name,
            'token_usage': token_usage,
            'output_ref': 'govoo.ai.suggestion,%s' % suggestion.id,
        })
        return suggestion

    def apply_to_record(self, record, attachment_id):
        """Run extraction for ``record``'s own model and pre-fill
        ``record``'s own in-memory fields directly from the result --
        used by each of the 6 target models' own document-field onchange
        (issue #233) so uploading/selecting a document auto-populates the
        form, with no separate "Scan Document" click and no popup wizard.

        Writes nothing to the database beyond the normal
        govoo.ai.request/govoo.ai.suggestion audit trail created by
        run() -- record's fields are only set on the in-memory,
        not-yet-saved record, exactly the same human-review gate (AI-N03)
        every other AI-F* feature already provides via its own explicit
        Apply/Accept step; here the "review" is simply looking at the
        pre-filled form before clicking Save.

        A relation field is only ever auto-filled on an exact, unique
        name match (AI-N02/AI-N04, same discipline as the wizard's
        _best_effort_match) -- anything else is left for the human,
        named in the returned warning.

        Returns an onchange-style ``{'title', 'message'}`` dict
        summarizing what was filled and what needs manual attention, or
        ``None`` if AI-F07 is disabled for this company, ``record``'s
        model is not a configured extraction target, or nothing in the
        document matched any known field -- in every one of those cases
        the caller's onchange does nothing further (the document field
        itself still gets set by the caller, same as it always did).
        """
        target_model = record._name
        if target_model not in EXTRACTION_FIELD_MAP:
            return None
        config = self.env['govoo.ai.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        if not config or not config.is_feature_enabled('ai_f07'):
            return None
        target_res_id = record.id if isinstance(record.id, int) else False
        suggestion = self.run(target_model, attachment_id, target_res_id=target_res_id)
        extracted = json.loads(suggestion.extracted_values or '{}')
        filled, unresolved = [], []
        for field_spec in EXTRACTION_FIELD_MAP[target_model]:
            name = field_spec['name']
            if name not in extracted:
                continue
            value = extracted[name]
            if field_spec['type'] == 'many2one':
                matches = self.env[field_spec['relation']].search(
                    [('name', '=ilike', value)], limit=2,
                )
                if len(matches) == 1:
                    record[name] = matches.id
                    filled.append(field_spec['label'])
                else:
                    unresolved.append('%s ("%s")' % (field_spec['label'], value))
                continue
            try:
                if field_spec['type'] == 'date':
                    record[name] = fields.Date.from_string(value)
                elif field_spec['type'] == 'integer':
                    record[name] = int(value)
                elif field_spec['type'] == 'monetary':
                    record[name] = float(value)
                else:
                    record[name] = value
            except (TypeError, ValueError):
                unresolved.append(field_spec['label'])
                continue
            filled.append(field_spec['label'])
        if not filled and not unresolved:
            return None
        message_parts = []
        if filled:
            message_parts.append(_(
                'AI pre-filled: %s. Review before saving.'
            ) % ', '.join(filled))
        if unresolved:
            message_parts.append(_(
                'Could not confidently set: %s. Please fill in manually.'
            ) % ', '.join(unresolved))
        return {'title': _('AI Extraction'), 'message': '\n'.join(message_parts)}

    def _build_system_prompt(self, target_model):
        lines = []
        for field in EXTRACTION_FIELD_MAP[target_model]:
            if field['type'] == 'many2one':
                lines.append(
                    '- %s (%s): the %s exactly as written in the document, '
                    'as plain text (e.g. a person or company name) -- '
                    'never a database id or a guessed reference number.'
                    % (field['name'], field['label'], field['label'])
                )
            elif field['type'] == 'selection':
                options = ', '.join(value for value, _label in field['selection'])
                lines.append(
                    '- %s (%s): one of exactly these values: %s'
                    % (field['name'], field['label'], options)
                )
            elif field['type'] == 'date':
                lines.append('- %s (%s): an ISO date, YYYY-MM-DD' % (field['name'], field['label']))
            elif field['type'] in ('integer', 'monetary'):
                lines.append(
                    '- %s (%s): a plain number, no currency symbol, no thousands separator'
                    % (field['name'], field['label'])
                )
            else:
                lines.append('- %s (%s): plain text' % (field['name'], field['label']))
        return (
            "You are a document data-extraction assistant for a corporate "
            "governance system. You are shown page image(s) of a scanned "
            "or executed document. Extract ONLY the following fields, "
            "exactly as stated in the document:\n\n%s\n\n"
            "If a field is not stated anywhere in the document, its value "
            "MUST be null -- never invent, guess, or infer a plausible "
            "value. Never resolve a name to a database id or code; always "
            "return names as plain text exactly as written. Respond with "
            "ONLY a JSON object mapping each field name above to its "
            "extracted value (or null), no other text, no extra keys."
        ) % '\n'.join(lines)

    def _parse_extracted(self, target_model, content):
        """Parse the model's JSON content into a {field: value} dict,
        keeping only known field names and dropping null values -- same
        "malformed/unexpected output degrades gracefully, never crashes"
        precedent as AI-F08's _parse_matches / AI-F09's _parse_answer.
        """
        try:
            parsed = json.loads(content or '{}')
        except ValueError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        known_fields = {field['name'] for field in EXTRACTION_FIELD_MAP[target_model]}
        return {
            name: value for name, value in parsed.items()
            if name in known_fields and value is not None and value != ''
        }

    def _attachment_to_images(self, attachment):
        """Return (list of base64-encoded page/image strings, mimetype).

        An image attachment is used as-is (its ``datas`` is already
        base64). A PDF is rendered page-by-page to PNG via PyMuPDF
        (``fitz``) -- a pure-Python renderer with no external system
        binary dependency (unlike pdf2image/poppler) -- capped at
        MAX_EXTRACTION_PAGES.

        :raise UserError: if the mimetype is unsupported, or the document
            is a PDF and PyMuPDF is not installed on this server.
        """
        mimetype = attachment.mimetype or ''
        if mimetype.startswith('image/'):
            datas = attachment.datas or b''
            return [datas.decode() if isinstance(datas, bytes) else datas], mimetype
        if mimetype == 'application/pdf':
            try:
                import fitz  # PyMuPDF
            except ImportError:
                raise UserError(_(
                    'PDF rendering is not available on this server '
                    '(PyMuPDF is not installed). Contact your administrator.'
                ))
            raw = base64.b64decode(attachment.datas or b'')
            images = []
            pdf = fitz.open(stream=raw, filetype='pdf')
            try:
                for page in list(pdf)[:MAX_EXTRACTION_PAGES]:
                    pixmap = page.get_pixmap()
                    images.append(base64.b64encode(pixmap.tobytes('png')).decode())
            finally:
                pdf.close()
            return images, 'image/png'
        raise UserError(_(
            'Unsupported document type for AI extraction: %s. Upload a '
            'PDF or image file.'
        ) % (mimetype or _('unknown')))
