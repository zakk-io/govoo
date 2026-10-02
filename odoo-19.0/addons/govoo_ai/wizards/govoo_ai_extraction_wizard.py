# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..models.govoo_ai_extraction import EXTRACTION_FIELD_MAP


class GovooAiExtractionWizard(models.TransientModel):
    """Extract Data from Document (AI-F07) -- one generic wizard for every
    extraction target in EXTRACTION_FIELD_MAP, rather than a near-duplicate
    wizard per model. A line editor (govoo.ai.extraction.wizard.line) shows
    one row per declared field, pre-filled from the AI's proposal but
    always human-editable before anything is written to a real record
    (AI-N02/AI-N03) -- never a silently-trusted auto-apply.
    """

    _name = 'govoo.ai.extraction.wizard'
    _description = 'Extract Data from Document (AI-F07)'

    target_model = fields.Selection(
        selection=lambda self: [(name, name) for name in EXTRACTION_FIELD_MAP],
        string='Extract Into',
        required=True,
    )
    target_res_id = fields.Integer(
        string='Existing Record ID',
        help='Set when extracting onto a record the user is already '
             'editing (e.g. backfilling a contract\'s dates) -- a smart '
             'button passes this in automatically. Left at 0, Apply '
             'proposes a brand-new record instead.',
    )
    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Document',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('extracted', 'Extracted'),
            ('applied', 'Applied'),
        ],
        default='draft',
    )
    suggestion_id = fields.Many2one(
        comodel_name='govoo.ai.suggestion',
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name='govoo.ai.extraction.wizard.line',
        inverse_name='wizard_id',
    )
    created_record_ref = fields.Reference(
        selection=lambda self: [(name, name) for name in EXTRACTION_FIELD_MAP],
        readonly=True,
    )

    @api.model
    def _open_for(self, target_model, target_res_id, attachment_id=False):
        """Build the act_window dict a target model's own "Scan Document"
        smart button returns -- shared so each of the six target models'
        own (tiny) button method doesn't repeat this shape."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extract Data from Document'),
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_target_model': target_model,
                'default_target_res_id': target_res_id,
                'default_attachment_id': attachment_id or False,
            },
        }

    def action_extract(self):
        self.ensure_one()
        suggestion = self.env['govoo.ai.extraction'].run(
            self.target_model, self.attachment_id.id, target_res_id=self.target_res_id,
        )
        extracted = json.loads(suggestion.extracted_values or '{}')
        line_vals = []
        for field_spec in EXTRACTION_FIELD_MAP[self.target_model]:
            value = extracted.get(field_spec['name'])
            vals = {
                'field_name': field_spec['name'],
                'field_label': field_spec['label'],
                'field_type': field_spec['type'],
            }
            if field_spec['type'] == 'many2one':
                vals['char_value'] = value or ''
                vals.update(self._best_effort_match(field_spec['relation'], value))
            else:
                vals['char_value'] = '' if value is None else str(value)
            line_vals.append((0, 0, vals))
        self.write({
            'suggestion_id': suggestion.id,
            'line_ids': [(5, 0, 0)] + line_vals,
            'state': 'extracted',
        })
        return self._reopen()

    def _best_effort_match(self, relation, extracted_name):
        """Suggest (never silently trust) a relation match for extracted
        free text -- AI-N02/AI-N04: the model's own output named a person
        or record, it did not resolve one, and only an exact, unique name
        match is ever pre-filled. Anything else is left for the human to
        pick via the real Many2one widget on the line."""
        resolved = self.env[relation]
        if extracted_name:
            matches = self.env[relation].search([('name', '=ilike', extracted_name)], limit=2)
            if len(matches) == 1:
                resolved = matches
        if relation == 'res.partner':
            return {'partner_value_id': resolved.id if resolved else False}
        if relation == 'govoo.share.class':
            return {'share_class_value_id': resolved.id if resolved else False}
        return {}

    def action_apply(self):
        self.ensure_one()
        if not self.suggestion_id:
            raise UserError(_('Run Extract before Apply.'))
        vals = {}
        for line in self.line_ids:
            value = line._coerce_value()
            if value is not None:
                vals[line.field_name] = value
        if not self.target_res_id:
            field_specs = EXTRACTION_FIELD_MAP[self.target_model]
            missing = [
                spec['label'] for spec in field_specs
                if spec['required'] and spec['name'] not in vals
            ]
            if missing:
                raise UserError(_(
                    'These required fields are missing before a new '
                    'record can be created: %s'
                ) % ', '.join(missing))
            record = self.env[self.target_model].create(vals)
        else:
            record = self.env[self.target_model].browse(self.target_res_id)
            if not record.exists():
                raise UserError(_('The record this extraction targets no longer exists.'))
            if vals:
                record.write(vals)
        self.suggestion_id.action_accept()
        self.suggestion_id.write({'target_res_id': record.id})
        self.write({
            'state': 'applied',
            'created_record_ref': '%s,%s' % (self.target_model, record.id),
        })
        return self._reopen()

    def action_open_record(self):
        self.ensure_one()
        if not self.created_record_ref:
            raise UserError(_('No record has been created or updated yet.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.created_record_ref._name,
            'res_id': self.created_record_ref.id,
            'views': [(False, 'form')],
            'target': 'current',
        }

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extract Data from Document'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class GovooAiExtractionWizardLine(models.TransientModel):
    """One proposed field value, editable before Apply. Exactly two typed
    relation columns (partner_value_id / share_class_value_id) cover every
    many2one relation that actually appears in EXTRACTION_FIELD_MAP --
    deliberately not a fully generic/dynamic relation widget, since the
    real set of relation targets today is small and known."""

    _name = 'govoo.ai.extraction.wizard.line'
    _description = 'AI Extraction Proposed Field (AI-F07)'

    wizard_id = fields.Many2one(
        comodel_name='govoo.ai.extraction.wizard',
        required=True,
        ondelete='cascade',
    )
    field_name = fields.Char(readonly=True)
    field_label = fields.Char(readonly=True)
    field_type = fields.Char(readonly=True)
    char_value = fields.Char(
        string='Value',
        help='Editable text for char/date/integer/monetary/selection '
             'fields. Ignored for many2one fields -- use the relation '
             'columns below instead.',
    )
    partner_value_id = fields.Many2one(
        comodel_name='res.partner',
        string='Match (Contact)',
    )
    share_class_value_id = fields.Many2one(
        comodel_name='govoo.share.class',
        string='Match (Share Class)',
    )

    def _coerce_value(self):
        """Return this line's value coerced to its declared field_type, or
        None if the human left it blank (meaning: do not set this field).

        :raise UserError: if a non-blank value cannot be coerced to its
            declared type (e.g. an unparsable date), naming the field so
            the human knows exactly what to fix.
        """
        self.ensure_one()
        if self.field_type == 'many2one':
            if self.partner_value_id:
                return self.partner_value_id.id
            if self.share_class_value_id:
                return self.share_class_value_id.id
            return None
        raw = (self.char_value or '').strip()
        if not raw:
            return None
        if self.field_type == 'date':
            try:
                return fields.Date.from_string(raw)
            except ValueError:
                raise UserError(_(
                    '"%(value)s" is not a valid date (expected YYYY-MM-DD) for %(field)s.'
                ) % {'value': raw, 'field': self.field_label})
        if self.field_type == 'integer':
            try:
                return int(raw)
            except ValueError:
                raise UserError(_(
                    '"%(value)s" is not a valid whole number for %(field)s.'
                ) % {'value': raw, 'field': self.field_label})
        if self.field_type == 'monetary':
            try:
                return float(raw)
            except ValueError:
                raise UserError(_(
                    '"%(value)s" is not a valid number for %(field)s.'
                ) % {'value': raw, 'field': self.field_label})
        return raw
