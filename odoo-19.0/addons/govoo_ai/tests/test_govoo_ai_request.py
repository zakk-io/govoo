# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooAiTestBase


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiRequest(GovooAiTestBase):

    def _make_request(self, feature='ai_f08', token_usage=0):
        return self.env['govoo.ai.request'].create({
            'feature': feature,
            'company_id': self.company.id,
            'token_usage': token_usage,
        })

    def test_request_blocked_without_config(self):
        with self.assertRaises(ValidationError):
            self._make_request()

    def test_request_blocked_when_ai_disabled(self):
        self.env['govoo.ai.config'].create({'company_id': self.company.id})
        with self.assertRaises(ValidationError):
            self._make_request()

    def test_request_blocked_when_feature_not_enabled(self):
        self._make_active_config(enabled_features=('ai_f09',))
        with self.assertRaises(ValidationError):
            self._make_request(feature='ai_f08')

    def test_request_succeeds_when_enabled(self):
        self._make_active_config(cap=1000, enabled_features=('ai_f08',))
        request = self._make_request()
        self.assertEqual(request.status, 'queued')

    def test_request_blocked_when_cap_reached(self):
        self._make_active_config(cap=100, enabled_features=('ai_f08',))
        self._make_request(token_usage=100)
        with self.assertRaises(ValidationError):
            self._make_request()

    def test_request_allowed_below_cap(self):
        self._make_active_config(cap=100, enabled_features=('ai_f08',))
        self._make_request(token_usage=50)
        # Should not raise -- 50 used out of a 100 cap.
        self._make_request(token_usage=10)

    def test_cron_process_queued_does_not_error_on_empty_queue(self):
        self.env['govoo.ai.request']._cron_process_queued()

    def test_cron_process_queued_leaves_requests_queued(self):
        self._make_active_config(cap=1000, enabled_features=('ai_f08',))
        request = self._make_request()
        self.env['govoo.ai.request']._cron_process_queued()
        self.assertEqual(request.status, 'queued')

    def test_other_company_isolated_from_request_log(self):
        self._make_active_config(cap=1000, enabled_features=('ai_f08',))
        request = self._make_request()
        other_company = self.env['res.company'].create({'name': 'Other Co'})
        self.ai_user.write({
            'company_ids': [(6, 0, [other_company.id])],
            'company_id': other_company.id,
        })
        found = self.env['govoo.ai.request'].with_user(self.ai_user).search([
            ('id', '=', request.id),
        ])
        self.assertFalse(found)
