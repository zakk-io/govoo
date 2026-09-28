# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooAiTestBase


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiSuggestion(GovooAiTestBase):

    def setUp(self):
        super().setUp()
        self._make_active_config(cap=1000, enabled_features=('ai_f08',))
        self.request = self.env['govoo.ai.request'].create({
            'feature': 'ai_f08',
            'company_id': self.company.id,
        })

    def _make_suggestion(self, **overrides):
        vals = {
            'request_id': self.request.id,
            'target_model': 'govoo.minutes',
        }
        vals.update(overrides)
        return self.env['govoo.ai.suggestion'].create(vals)

    def test_default_state_is_pending(self):
        suggestion = self._make_suggestion()
        self.assertEqual(suggestion.state, 'pending')
        self.assertFalse(suggestion.reviewed_by)

    def test_direct_write_to_state_blocked(self):
        suggestion = self._make_suggestion()
        with self.assertRaises(ValidationError):
            suggestion.write({'state': 'accepted'})

    def test_action_accept_sets_state_and_reviewer(self):
        suggestion = self._make_suggestion()
        suggestion.action_accept()
        self.assertEqual(suggestion.state, 'accepted')
        self.assertEqual(suggestion.reviewed_by, self.env.user)
        self.assertTrue(suggestion.reviewed_date)

    def test_action_reject_sets_state_and_reviewer(self):
        suggestion = self._make_suggestion()
        suggestion.action_reject()
        self.assertEqual(suggestion.state, 'rejected')
        self.assertEqual(suggestion.reviewed_by, self.env.user)

    def test_cannot_accept_a_non_pending_suggestion_twice(self):
        suggestion = self._make_suggestion()
        suggestion.action_accept()
        with self.assertRaises(ValidationError):
            suggestion.action_accept()

    def test_cannot_reject_an_already_accepted_suggestion(self):
        suggestion = self._make_suggestion()
        suggestion.action_accept()
        with self.assertRaises(ValidationError):
            suggestion.action_reject()

    def test_confidence_out_of_range_raises(self):
        with self.assertRaises(ValidationError):
            self._make_suggestion(confidence=1.5)

    def test_confidence_negative_raises(self):
        with self.assertRaises(ValidationError):
            self._make_suggestion(confidence=-0.1)

    def test_non_state_write_is_not_blocked(self):
        suggestion = self._make_suggestion()
        suggestion.write({'target_res_id': 42})
        self.assertEqual(suggestion.target_res_id, 42)
