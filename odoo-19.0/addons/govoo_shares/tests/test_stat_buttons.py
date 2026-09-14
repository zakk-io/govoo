# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestShareClassStatButtons(TransactionCase):
    """Test share class stat buttons and computed count fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Shareholder',
        })
        cls.share_class = cls.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'company_id': cls.company.id,
            'nominal_value': 100,
            'total_authorised': 1000,
        })

    def test_allotment_count(self):
        """Share class allotment_count computes correctly."""
        self.assertEqual(self.share_class.allotment_count, 0)
        self.env['govoo.share.allotment'].create({
            'share_class_id': self.share_class.id,
            'partner_id': self.partner.id,
            'quantity': 100,
            'company_id': self.company.id,
        })
        self.share_class.invalidate_recordset(['allotment_count'])
        self.assertEqual(self.share_class.allotment_count, 1)

    def test_transfer_count(self):
        """Share class transfer_count computes correctly."""
        self.assertEqual(self.share_class.transfer_count, 0)
        # Create allotment first
        allotment = self.env['govoo.share.allotment'].create({
            'share_class_id': self.share_class.id,
            'partner_id': self.partner.id,
            'quantity': 100,
            'company_id': self.company.id,
        })
        partner_b = self.env['res.partner'].create({'name': 'Transfer Recipient'})
        self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner.id,
            'transferee_id': partner_b.id,
            'quantity': 50,
            'company_id': self.company.id,
        })
        self.share_class.invalidate_recordset(['transfer_count'])
        self.assertEqual(self.share_class.transfer_count, 1)

    def test_holding_count(self):
        """Share class holding_count computes correctly."""
        self.assertEqual(self.share_class.holding_count, 0)
        self.env['govoo.share.holding'].create({
            'share_class_id': self.share_class.id,
            'partner_id': self.partner.id,
            'quantity': 100,
            'company_id': self.company.id,
        })
        self.share_class.invalidate_recordset(['holding_count'])
        self.assertEqual(self.share_class.holding_count, 1)

    def test_action_view_allotments(self):
        """action_view_allotments returns correct action."""
        action = self.share_class.action_view_allotments()
        self.assertEqual(action['res_model'], 'govoo.share.allotment')
        self.assertEqual(action['domain'], [('share_class_id', '=', self.share_class.id)])

    def test_action_view_transfers(self):
        """action_view_transfers returns correct action."""
        action = self.share_class.action_view_transfers()
        self.assertEqual(action['res_model'], 'govoo.share.transfer')
        self.assertEqual(action['domain'], [('share_class_id', '=', self.share_class.id)])

    def test_action_view_holders(self):
        """action_view_holders returns correct action."""
        action = self.share_class.action_view_holders()
        self.assertEqual(action['res_model'], 'govoo.share.holding')
        self.assertEqual(action['domain'], [('share_class_id', '=', self.share_class.id)])
