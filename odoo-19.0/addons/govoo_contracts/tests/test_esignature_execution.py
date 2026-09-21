# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestEsignatureExecution(GovooContractsTestBase):
    """E-signature Execution (issue #172): BR-CM-005.

    Reuses the exact same Rwandan legal-validity confirmation flag as
    govoo_board's BR-BOARD-008 (docs/spec/integrations/sign.md), rather
    than a separate contract-specific one.
    """

    def setUp(self):
        super().setUp()
        self.attachment = self.env['ir.attachment'].create({
            'name': 'sign-request.pdf', 'raw': b'stub',
        })

    def test_sign_request_blocked_without_legal_confirmation(self):
        contract = self._make_contract()
        with self.assertRaises(ValidationError):
            contract.write({'sign_request_id': self.attachment.id})

    def test_sign_request_allowed_once_legally_confirmed(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        contract = self._make_contract()
        contract.write({'sign_request_id': self.attachment.id})
        self.assertEqual(contract.sign_request_id, self.attachment)

    def test_confirmation_flag_is_shared_with_govoo_board(self):
        """A confirmation already recorded for govoo_board (minutes/
        resolutions) also unblocks contracts -- BR-CM-005 is one shared
        gate, not a second independent one."""
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('govoo_board.e_signature_legally_confirmed', 'True')
        contract = self._make_contract()
        contract.write({'sign_request_id': self.attachment.id})
        self.assertEqual(contract.sign_request_id, self.attachment)

    def test_manual_upload_path_unaffected_by_confirmation_flag(self):
        """The manual signed-copy path (executed_document_id) never
        depends on the e-signature legal-validity flag -- it's always
        available, confirmed or not."""
        self._grant_delegation()
        contract = self._make_contract(executed_document_id=self.attachment.id)
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        self.assertEqual(contract.state, 'executed')
        self.assertEqual(contract.executed_document_id, self.attachment)
