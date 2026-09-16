# Part of Govoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo.tests import tagged

from .common import GovooComplianceTestBase


@tagged('post_install', '-at_install', 'govoo_compliance')
class GovooComplianceFilingDocumentTC(GovooComplianceTestBase):
    """Issue #53: filing_document_id (spec) vs attachment_id (dead
    duplicate) -- action_generate_filing_pack() must write to the
    spec-documented field name."""

    def test_attachment_id_field_removed(self):
        self.assertNotIn('attachment_id', self.env['govoo.compliance.instance']._fields)

    def test_generate_filing_pack_sets_filing_document_id(self):
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
        instance = self.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': self.company.id,
            'due_date': '2026-03-31',
        })
        instance.action_start()
        instance.action_generate_filing_pack()
        self.assertTrue(
            instance.filing_document_id,
            'action_generate_filing_pack() should set filing_document_id.',
        )
        # Regression guard: same base64-encoding bug class as
        # govoo_board_pack.py's _generate_document (see the detailed
        # comment in test_board_pack.py for why this checks decoded
        # UTF-8 content rather than a %PDF- header -- forcing real
        # wkhtmltopdf rendering deadlocks this single-worker test
        # server).
        content = base64.b64decode(instance.filing_document_id.datas).decode('utf-8')
        self.assertIn(
            'Filing Pack', content,
            'The generated filing pack attachment content is corrupted (not valid decoded report output).',
        )
