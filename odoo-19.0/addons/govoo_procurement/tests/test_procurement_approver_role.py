# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestProcurementApproverRole(GovooProcurementTestBase):
    """Issue #317: a Procurement Approver can review a tender and award it
    through a narrow wizard, but never create a tender, edit a bid, or
    enter a score -- and can never award a tender they created themselves
    (issue #300's second-reviewer gate)."""

    def _make_approver(self, login):
        return new_test_user(
            self.env, login=login,
            groups='govoo_procurement.group_govoo_procurement_approver',
            company_id=self.company.id,
        )

    def test_approver_can_award_via_wizard(self):
        approver = self._make_approver('test_procurement_approver_award')
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        tender.action_start_technical_evaluation()
        tender.action_start_financial_evaluation()

        wizard = self.env['govoo.tender.award.wizard'].with_user(approver).create({
            'tender_id': tender.id,
            'awarded_bid_id': bid.id,
        })
        wizard.action_submit()

        self.assertEqual(tender.evaluation_stage, 'awarded')
        self.assertEqual(tender.awarded_bid_id, bid)

    def test_tender_creator_cannot_award_even_with_approver_group(self):
        """The #300 check is role-agnostic: holding the Approver group
        doesn't matter if you're also the one who created this tender."""
        officer_approver = new_test_user(
            self.env, login='test_procurement_officer_approver',
            groups='govoo_procurement.group_govoo_procurement_officer,'
                   'govoo_procurement.group_govoo_procurement_approver',
            company_id=self.company.id,
        )
        tender = self.env['govoo.tender'].with_user(officer_approver).create({
            'name': 'Solo Tender',
            'company_id': self.company.id,
        })
        bid = self.env['purchase.order'].with_user(officer_approver).create({
            'partner_id': self.vendor_a.id,
            'govoo_tender_id': tender.id,
            'company_id': self.company.id,
        })
        tender.with_user(officer_approver).action_start_technical_evaluation()
        tender.with_user(officer_approver).action_start_financial_evaluation()

        wizard = self.env['govoo.tender.award.wizard'].with_user(officer_approver).create({
            'tender_id': tender.id,
            'awarded_bid_id': bid.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_submit()

    def test_approver_cannot_write_awarded_bid_directly(self):
        approver = self._make_approver('test_procurement_approver_direct_write')
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        with self.assertRaises(AccessError):
            tender.with_user(approver).write({'awarded_bid_id': bid.id})

    def test_approver_cannot_create_tender_or_enter_score(self):
        approver = self._make_approver('test_procurement_approver_create')
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        with self.assertRaises(AccessError):
            self.env['govoo.tender'].with_user(approver).create({
                'name': 'New Tender',
                'company_id': self.company.id,
            })
        with self.assertRaises(AccessError):
            bid.with_user(approver).write({'govoo_technical_score': 50})

    def test_non_approver_cannot_use_award_wizard(self):
        plain_user = new_test_user(
            self.env, login='test_procurement_plain_user_award',
            groups='govoo_base.group_govoo_user',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        tender.action_start_technical_evaluation()
        tender.action_start_financial_evaluation()

        with self.assertRaises(AccessError):
            self.env['govoo.tender.award.wizard'].with_user(plain_user).create({
                'tender_id': tender.id,
                'awarded_bid_id': bid.id,
            })

        wizard = self.env['govoo.tender.award.wizard'].create({
            'tender_id': tender.id,
            'awarded_bid_id': bid.id,
        })
        with self.assertRaises(AccessError):
            wizard.with_user(plain_user).action_submit()
