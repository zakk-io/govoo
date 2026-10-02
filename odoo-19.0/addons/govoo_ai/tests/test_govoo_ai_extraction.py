# Part of Govoo. See LICENSE file for full copyright and licensing details.

import base64
import json
from unittest import mock

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import GovooAiTestBase

_FAKE_PNG = base64.b64encode(b'\x89PNG\r\n\x1a\nfake-image-bytes')


def _extraction_response(values, tokens=10):
    return {
        'model': 'gpt-4o-mini',
        'choices': [{'message': {
            'role': 'assistant',
            'content': json.dumps(values),
        }}],
        'usage': {'total_tokens': tokens},
    }


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiExtraction(GovooAiTestBase):

    def setUp(self):
        super().setUp()
        self._make_active_config(cap=100000, enabled_features=('ai_f07',))
        self.attachment = self.env['ir.attachment'].create({
            'name': 'appointment_letter.png',
            'datas': _FAKE_PNG,
            'mimetype': 'image/png',
        })

    def _patch_chat_completion(self, side_effect):
        return mock.patch.object(
            type(self.env['govoo.ai.openai.client']),
            'chat_completion',
            side_effect=side_effect,
        )

    def test_run_raises_when_feature_not_enabled(self):
        self.env['govoo.ai.config'].search([]).write({'ai_f07': False})
        with self.assertRaises(UserError):
            self.env['govoo.ai.extraction'].run('govoo.appointment', self.attachment.id)

    def test_run_raises_for_unsupported_target_model(self):
        with self.assertRaises(UserError):
            self.env['govoo.ai.extraction'].run('res.partner', self.attachment.id)

    def test_run_raises_when_attachment_not_found(self):
        with self.assertRaises(UserError):
            self.env['govoo.ai.extraction'].run('govoo.appointment', 999999999)

    def test_run_raises_when_attachment_not_readable(self):
        with mock.patch.object(
            type(self.env['ir.attachment']), 'check_access', side_effect=AccessError('denied'),
        ):
            with self.assertRaises(UserError):
                self.env['govoo.ai.extraction'].run('govoo.appointment', self.attachment.id)

    def test_run_creates_suggestion_with_extracted_values(self):
        response = _extraction_response({
            'partner_id': 'Jane Doe',
            'role': 'director',
            'date_appointed': '2026-03-01',
            'date_resigned': None,
        })
        with self._patch_chat_completion(side_effect=[response]):
            suggestion = self.env['govoo.ai.extraction'].run('govoo.appointment', self.attachment.id)
        self.assertEqual(suggestion.target_model, 'govoo.appointment')
        self.assertFalse(suggestion.target_res_id)
        self.assertEqual(suggestion.request_id.status, 'done')
        self.assertEqual(suggestion.request_id.feature, 'ai_f07')
        extracted = json.loads(suggestion.extracted_values)
        self.assertEqual(extracted['partner_id'], 'Jane Doe')
        self.assertEqual(extracted['role'], 'director')
        self.assertEqual(extracted['date_appointed'], '2026-03-01')
        self.assertNotIn('date_resigned', extracted)  # null values are dropped

    def test_run_drops_unknown_keys_from_model_output(self):
        response = _extraction_response({
            'partner_id': 'Jane Doe',
            'role': 'director',
            'date_appointed': '2026-03-01',
            'ssn': '123-45-6789',  # not in EXTRACTION_FIELD_MAP -- must never be kept
        })
        with self._patch_chat_completion(side_effect=[response]):
            suggestion = self.env['govoo.ai.extraction'].run('govoo.appointment', self.attachment.id)
        extracted = json.loads(suggestion.extracted_values)
        self.assertNotIn('ssn', extracted)

    def test_run_tolerates_malformed_json_as_no_extracted_values(self):
        response = {
            'model': 'gpt-4o-mini',
            'choices': [{'message': {'content': 'not valid json at all'}}],
            'usage': {'total_tokens': 3},
        }
        with self._patch_chat_completion(side_effect=[response]):
            suggestion = self.env['govoo.ai.extraction'].run('govoo.appointment', self.attachment.id)
        self.assertEqual(json.loads(suggestion.extracted_values), {})
        self.assertEqual(suggestion.request_id.status, 'done')

    def test_run_marks_request_failed_on_provider_error(self):
        # Deliberately not self.assertRaises -- see test_govoo_ai_search.py's
        # identical note on TransactionCase.assertRaises' savepoint rollback.
        with self._patch_chat_completion(side_effect=RuntimeError('provider down')):
            try:
                self.env['govoo.ai.extraction'].run('govoo.appointment', self.attachment.id)
                self.fail('Expected a RuntimeError from the patched chat_completion')
            except RuntimeError:
                pass
        request = self.env['govoo.ai.request'].search(
            [('feature', '=', 'ai_f07')], order='id desc', limit=1,
        )
        self.assertEqual(request.status, 'failed')

    def test_run_accepts_an_existing_target_res_id(self):
        contract_attachment = self.env['ir.attachment'].create({
            'name': 'executed_contract.png',
            'datas': _FAKE_PNG,
            'mimetype': 'image/png',
        })
        response = _extraction_response({'date_end': '2027-01-01'})
        with self._patch_chat_completion(side_effect=[response]):
            suggestion = self.env['govoo.ai.extraction'].run(
                'govoo.contract', contract_attachment.id, target_res_id=42,
            )
        self.assertEqual(suggestion.target_res_id, 42)

    def test_attachment_to_images_rejects_unsupported_mimetype(self):
        bad_attachment = self.env['ir.attachment'].create({
            'name': 'notes.txt',
            'datas': base64.b64encode(b'plain text'),
            'mimetype': 'text/plain',
        })
        with self.assertRaises(UserError):
            self.env['govoo.ai.extraction']._attachment_to_images(bad_attachment)

    def test_attachment_to_images_reports_missing_pdf_library_clearly(self):
        pdf_attachment = self.env['ir.attachment'].create({
            'name': 'contract.pdf',
            'datas': base64.b64encode(b'%PDF-1.4 fake'),
            'mimetype': 'application/pdf',
        })
        try:
            import fitz  # noqa: F401
            self.skipTest('PyMuPDF is installed in this environment -- '
                           'covered instead by test_pdf_page_cap_is_enforced')
        except ImportError:
            pass
        with self.assertRaises(UserError):
            self.env['govoo.ai.extraction']._attachment_to_images(pdf_attachment)


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiExtractionWizard(GovooAiTestBase):

    def setUp(self):
        super().setUp()
        self._make_active_config(cap=100000, enabled_features=('ai_f07',))
        self.attachment = self.env['ir.attachment'].create({
            'name': 'appointment_letter.png',
            'datas': _FAKE_PNG,
            'mimetype': 'image/png',
        })
        self.partner = self.env['res.partner'].create({'name': 'Jane Doe'})

    def _patch_chat_completion(self, side_effect):
        return mock.patch.object(
            type(self.env['govoo.ai.openai.client']),
            'chat_completion',
            side_effect=side_effect,
        )

    def test_uploading_a_file_creates_and_selects_an_attachment(self):
        wizard = self.env['govoo.ai.extraction.wizard'].new({
            'target_model': 'govoo.appointment',
        })
        wizard.document = _FAKE_PNG
        wizard.document_filename = 'scanned_letter.png'
        wizard._onchange_document()
        self.assertTrue(wizard.attachment_id)
        self.assertEqual(wizard.attachment_id.name, 'scanned_letter.png')
        self.assertFalse(wizard.document)  # cleared after creating the attachment

    def test_extract_then_apply_creates_a_new_record(self):
        response = _extraction_response({
            'partner_id': 'Jane Doe',
            'role': 'director',
            'date_appointed': '2026-03-01',
        })
        wizard = self.env['govoo.ai.extraction.wizard'].create({
            'target_model': 'govoo.appointment',
            'attachment_id': self.attachment.id,
        })
        with self._patch_chat_completion(side_effect=[response]):
            wizard.action_extract()
        self.assertEqual(wizard.state, 'extracted')
        partner_line = wizard.line_ids.filtered(lambda line: line.field_name == 'partner_id')
        self.assertEqual(partner_line.partner_value_id, self.partner)  # exact-name auto-match
        wizard.action_apply()
        self.assertEqual(wizard.state, 'applied')
        appointment = self.env['govoo.appointment'].browse(wizard.created_record_ref.id)
        self.assertEqual(appointment.partner_id, self.partner)
        self.assertEqual(appointment.role, 'director')
        self.assertEqual(str(appointment.date_appointed), '2026-03-01')
        self.assertEqual(wizard.suggestion_id.state, 'accepted')
        self.assertEqual(wizard.suggestion_id.target_res_id, appointment.id)

    def test_apply_blocks_new_record_missing_a_required_field(self):
        response = _extraction_response({'role': 'director'})  # partner_id/date_appointed missing
        wizard = self.env['govoo.ai.extraction.wizard'].create({
            'target_model': 'govoo.appointment',
            'attachment_id': self.attachment.id,
        })
        with self._patch_chat_completion(side_effect=[response]):
            wizard.action_extract()
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_apply_writes_onto_an_existing_record(self):
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'role': 'director',
            'date_appointed': '2025-01-01',
        })
        response = _extraction_response({'date_resigned': '2026-06-30'})
        wizard = self.env['govoo.ai.extraction.wizard'].create({
            'target_model': 'govoo.appointment',
            'target_res_id': appointment.id,
            'attachment_id': self.attachment.id,
        })
        with self._patch_chat_completion(side_effect=[response]):
            wizard.action_extract()
        wizard.action_apply()
        self.assertEqual(str(appointment.date_resigned), '2026-06-30')
        self.assertEqual(wizard.suggestion_id.target_res_id, appointment.id)

    def test_apply_rejects_an_unparsable_date(self):
        response = _extraction_response({
            'partner_id': 'Jane Doe', 'role': 'director', 'date_appointed': 'not-a-date',
        })
        wizard = self.env['govoo.ai.extraction.wizard'].create({
            'target_model': 'govoo.appointment',
            'attachment_id': self.attachment.id,
        })
        with self._patch_chat_completion(side_effect=[response]):
            wizard.action_extract()
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_blank_line_is_left_unset_rather_than_blocking_apply(self):
        response = _extraction_response({
            'partner_id': 'Jane Doe', 'role': 'director', 'date_appointed': '2026-03-01',
        })
        wizard = self.env['govoo.ai.extraction.wizard'].create({
            'target_model': 'govoo.appointment',
            'attachment_id': self.attachment.id,
        })
        with self._patch_chat_completion(side_effect=[response]):
            wizard.action_extract()
        resigned_line = wizard.line_ids.filtered(lambda line: line.field_name == 'date_resigned')
        self.assertFalse(resigned_line.char_value)
        wizard.action_apply()  # must not raise despite the blank optional field
        appointment = self.env['govoo.appointment'].browse(wizard.created_record_ref.id)
        self.assertFalse(appointment.date_resigned)
