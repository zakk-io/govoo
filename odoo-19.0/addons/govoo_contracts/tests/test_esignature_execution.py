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


@tagged('post_install', '-at_install')
class TestEsignatureOptionalToggleAndWorkflow(GovooContractsTestBase):
    """Optional E-Signature Toggle & Send-for-Signature Workflow
    (issue #199): a business-level opt-in per contract type, separate
    from and in addition to the BR-CM-005 legal-confirmation gate, plus
    the actual send/mark-signed/declined/cancel lifecycle that the
    Sign Request field previously had no workflow around at all."""

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        self.attachment = self.env['ir.attachment'].create({
            'name': 'sign-request.pdf', 'raw': b'stub',
        })

    def test_e_signature_disabled_by_default_on_new_type(self):
        self.assertFalse(self.contract_type.e_signature_enabled)

    def test_send_blocked_when_type_does_not_enable_e_signature(self):
        contract = self._make_contract(sign_request_id=self.attachment.id)
        with self.assertRaises(ValidationError):
            contract.action_send_for_signature()

    def test_legal_confirmation_alone_does_not_bypass_the_toggle(self):
        """Even though the global legal-confirmation flag is True (set in
        setUp), a contract type that hasn't opted in via
        e_signature_enabled still blocks sending -- the toggle is an
        additional restriction, never a way around the legal gate, and
        the legal gate is never a way around the toggle either."""
        self.contract_type.e_signature_enabled = False
        contract = self._make_contract(sign_request_id=self.attachment.id)
        with self.assertRaises(ValidationError):
            contract.action_send_for_signature()

    def test_send_blocked_without_a_document_attached(self):
        self.contract_type.e_signature_enabled = True
        contract = self._make_contract()
        with self.assertRaises(ValidationError):
            contract.action_send_for_signature()

    def test_send_succeeds_when_enabled_and_document_attached(self):
        self.contract_type.e_signature_enabled = True
        contract = self._make_contract(sign_request_id=self.attachment.id)
        contract.action_send_for_signature()
        self.assertEqual(contract.sign_status, 'sent')

    def test_mark_signed_from_sent(self):
        self.contract_type.e_signature_enabled = True
        contract = self._make_contract(sign_request_id=self.attachment.id)
        contract.action_send_for_signature()
        contract.action_mark_signed()
        self.assertEqual(contract.sign_status, 'signed')

    def test_mark_declined_from_sent(self):
        self.contract_type.e_signature_enabled = True
        contract = self._make_contract(sign_request_id=self.attachment.id)
        contract.action_send_for_signature()
        contract.action_mark_declined()
        self.assertEqual(contract.sign_status, 'declined')

    def test_cancel_from_sent_and_resend(self):
        self.contract_type.e_signature_enabled = True
        contract = self._make_contract(sign_request_id=self.attachment.id)
        contract.action_send_for_signature()
        contract.action_cancel_signature()
        self.assertEqual(contract.sign_status, 'cancelled')
        contract.action_send_for_signature()
        self.assertEqual(contract.sign_status, 'sent')

    def test_cannot_mark_signed_without_sending_first(self):
        self.contract_type.e_signature_enabled = True
        contract = self._make_contract(sign_request_id=self.attachment.id)
        with self.assertRaises(ValidationError):
            contract.action_mark_signed()

    def test_cannot_send_twice_while_already_sent(self):
        self.contract_type.e_signature_enabled = True
        contract = self._make_contract(sign_request_id=self.attachment.id)
        contract.action_send_for_signature()
        with self.assertRaises(ValidationError):
            contract.action_send_for_signature()
