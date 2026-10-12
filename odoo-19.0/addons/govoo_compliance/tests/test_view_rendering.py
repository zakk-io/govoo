# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooComplianceTestBase


@tagged('post_install', '-at_install', 'govoo_compliance')
class TestComplianceViewRendering(GovooComplianceTestBase):
    """Issue #253: get_views() exercises the same field/widget validation
    Odoo runs on module upgrade, so a ribbon or tooltip referencing a
    renamed/typo'd field would fail here too, not just at -u time."""

    def _make_instance(self, **overrides):
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Annual Return',
            'authority': 'RDB',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 31,
            'fixed_month': 3,
            'active': True,
            'company_id': self.company.id,
        })
        vals = {
            'obligation_id': obligation.id,
            'company_id': self.company.id,
            'due_date': '2026-03-31',
        }
        vals.update(overrides)
        return self.env['govoo.compliance.instance'].create(vals)

    def test_instance_form_view_loads_when_filed(self):
        instance = self._make_instance()
        instance.action_start()
        instance.write({'reference_no': 'REF-001', 'filed_date': '2026-03-20'})
        instance.action_file()
        self.assertEqual(instance.state, 'filed')
        instance.get_views([(False, 'form')])

    def test_instance_form_view_loads_when_waived(self):
        instance = self._make_instance()
        instance.action_waive()
        self.assertEqual(instance.state, 'waived')
        instance.get_views([(False, 'form')])

    def test_obligation_form_view_loads(self):
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'VAT Return',
            'authority': 'RRA',
            'frequency': 'monthly',
            'basis': 'fye_relative',
            'fye_offset_months': 2,
            'active': True,
            'company_id': self.company.id,
        })
        obligation.get_views([(False, 'form')])
