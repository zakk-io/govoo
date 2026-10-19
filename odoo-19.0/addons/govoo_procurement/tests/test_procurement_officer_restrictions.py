# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestProcurementOfficerRestrictions(GovooProcurementTestBase):
    """Issue #318: now that dedicated Evaluator and Approver roles exist
    (#316, #317), the Procurement Officer loses the two abilities those
    roles took over -- entering a bid score and awarding a tender -- while
    keeping everything else (create tender, add/edit bids, move stages)."""

    def _make_officer(self, login):
        return new_test_user(
            self.env, login=login,
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=self.company.id,
        )

    def test_officer_cannot_write_score_directly(self):
        officer = self._make_officer('test_officer_restrict_write')
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        with self.assertRaises(AccessError):
            bid.with_user(officer).write({'govoo_technical_score': 50})

    def test_officer_cannot_create_bid_with_score_preset(self):
        officer = self._make_officer('test_officer_restrict_create')
        tender = self._make_tender()

        with self.assertRaises(AccessError):
            self.env['purchase.order'].with_user(officer).create({
                'partner_id': self.vendor_a.id,
                'govoo_tender_id': tender.id,
                'company_id': self.company.id,
                'govoo_technical_score': 50,
            })

    def test_officer_cannot_award_tender(self):
        creator = self._make_officer('test_officer_restrict_award_creator')
        other_officer = self._make_officer('test_officer_restrict_award_other')
        tender = self.env['govoo.tender'].with_user(creator).create({
            'name': 'Solo Tender',
            'company_id': self.company.id,
        })
        bid = self.env['purchase.order'].with_user(creator).create({
            'partner_id': self.vendor_a.id,
            'govoo_tender_id': tender.id,
            'company_id': self.company.id,
        })
        tender.with_user(creator).action_start_technical_evaluation()
        tender.with_user(creator).action_start_financial_evaluation()
        tender.with_user(creator).write({'awarded_bid_id': bid.id})

        # A *different* officer than the tender's creator still can't
        # award it -- this is the role restriction (#318), not the
        # creator-can't-approve-their-own-tender rule (#300).
        with self.assertRaises(AccessError):
            tender.with_user(other_officer).action_award()

    def test_officer_can_still_run_the_tender_process(self):
        """No regression: everything except scoring and awarding still
        works for the Officer."""
        officer = self._make_officer('test_officer_restrict_smoke')
        tender = self.env['govoo.tender'].with_user(officer).create({
            'name': 'Still Works Tender',
            'company_id': self.company.id,
        })
        bid = self.env['purchase.order'].with_user(officer).create({
            'partner_id': self.vendor_a.id,
            'govoo_tender_id': tender.id,
            'company_id': self.company.id,
        })
        tender.with_user(officer).action_start_technical_evaluation()
        tender.with_user(officer).action_start_financial_evaluation()

        self.assertEqual(tender.evaluation_stage, 'financial_evaluation')
        self.assertEqual(bid.govoo_tender_id, tender)
