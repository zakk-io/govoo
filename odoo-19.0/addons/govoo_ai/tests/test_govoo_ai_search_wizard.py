# Part of Govoo. See LICENSE file for full copyright and licensing details.

from unittest import mock

from odoo.tests import tagged

from .common import GovooAiTestBase
from .test_govoo_ai_search import _final_response


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiSearchWizard(GovooAiTestBase):

    def setUp(self):
        super().setUp()
        self._make_active_config(cap=100000, enabled_features=('ai_f08',))
        self.target = self.env['res.partner'].create({'name': 'Findable Partner'})

    def test_action_search_populates_results(self):
        wizard = self.env['govoo.ai.search.wizard'].create({'query': 'Findable Partner'})
        response = _final_response([
            {'model': 'res.partner', 'res_id': self.target.id, 'reason': 'matched'},
        ])
        with mock.patch.object(
            type(self.env['govoo.ai.openai.client']),
            'chat_completion',
            side_effect=[response],
        ):
            wizard.action_search()
        self.assertEqual(wizard.state, 'done')
        self.assertEqual(len(wizard.result_ids), 1)
        self.assertTrue(wizard.request_id)

    def test_action_reset_clears_state(self):
        wizard = self.env['govoo.ai.search.wizard'].create({'query': 'anything'})
        wizard.write({'state': 'done'})
        wizard.action_reset()
        self.assertEqual(wizard.state, 'draft')
        self.assertFalse(wizard.query)
        self.assertFalse(wizard.result_ids)
