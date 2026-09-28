# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import GovooAiTestBase


def _final_response(matches, tokens=10):
    return {
        'model': 'gpt-4o-mini',
        'choices': [{'message': {
            'role': 'assistant',
            'content': json.dumps({'matches': matches}),
        }}],
        'usage': {'total_tokens': tokens},
    }


def _tool_call_response(tool_name='search_count', arguments=None, tokens=5):
    return {
        'model': 'gpt-4o-mini',
        'choices': [{'message': {
            'role': 'assistant',
            'tool_calls': [{
                'id': 'call_1',
                'function': {
                    'name': tool_name,
                    'arguments': json.dumps(arguments or {'model': 'res.partner', 'domain': []}),
                },
            }],
        }}],
        'usage': {'total_tokens': tokens},
    }


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiSearch(GovooAiTestBase):

    def setUp(self):
        super().setUp()
        self._make_active_config(cap=100000, enabled_features=('ai_f08',))
        self.target = self.env['res.partner'].create({'name': 'Findable Partner'})

    def _patch_chat_completion(self, side_effect):
        return mock.patch.object(
            type(self.env['govoo.ai.openai.client']),
            'chat_completion',
            side_effect=side_effect,
        )

    def test_run_raises_when_feature_not_enabled(self):
        self.env['govoo.ai.config'].search([]).write({'ai_f08': False})
        with self.assertRaises(UserError):
            self.env['govoo.ai.search'].run('anything')

    def test_run_raises_on_empty_query(self):
        with self.assertRaises(UserError):
            self.env['govoo.ai.search'].run('   ')

    def test_run_creates_suggestion_for_readable_match(self):
        response = _final_response([
            {'model': 'res.partner', 'res_id': self.target.id, 'reason': 'Name matches the query.'},
        ])
        with self._patch_chat_completion(side_effect=[response]):
            suggestions = self.env['govoo.ai.search'].run('Findable Partner')
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions.target_model, 'res.partner')
        self.assertEqual(suggestions.target_res_id, self.target.id)
        self.assertEqual(suggestions.request_id.status, 'done')
        self.assertEqual(suggestions.request_id.feature, 'ai_f08')
        self.assertTrue(suggestions.request_id.token_usage)

    def test_run_drops_match_for_nonexistent_record(self):
        response = _final_response([
            {'model': 'res.partner', 'res_id': 999999999, 'reason': 'hallucinated'},
        ])
        with self._patch_chat_completion(side_effect=[response]):
            suggestions = self.env['govoo.ai.search'].run('query')
        self.assertFalse(suggestions)

    def test_run_drops_match_for_unknown_model(self):
        response = _final_response([
            {'model': 'not.a.real.model', 'res_id': 1, 'reason': 'hallucinated'},
        ])
        with self._patch_chat_completion(side_effect=[response]):
            suggestions = self.env['govoo.ai.search'].run('query')
        self.assertFalse(suggestions)

    def test_run_returns_empty_when_nothing_matches(self):
        with self._patch_chat_completion(side_effect=[_final_response([])]):
            suggestions = self.env['govoo.ai.search'].run('query')
        self.assertFalse(suggestions)

    def test_run_dispatches_tool_call_before_final_answer(self):
        responses = [
            _tool_call_response(),
            _final_response([
                {'model': 'res.partner', 'res_id': self.target.id, 'reason': 'found via search_count'},
            ]),
        ]
        with self._patch_chat_completion(side_effect=responses):
            suggestions = self.env['govoo.ai.search'].run('query')
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions.request_id.token_usage, 15)  # 5 + 10

    def test_run_raises_when_loop_does_not_converge(self):
        with self._patch_chat_completion(side_effect=lambda **kw: _tool_call_response()):
            with self.assertRaises(UserError):
                self.env['govoo.ai.search'].run('query')

    def test_request_marked_failed_on_error(self):
        # Deliberately not using self.assertRaises here: Odoo's
        # TransactionCase.assertRaises wraps its block in a savepoint and
        # rolls back to it once the expected exception fires (so exception
        # tests don't leave stray data behind), which would also erase the
        # govoo.ai.request row this test needs to inspect afterwards.
        with self._patch_chat_completion(side_effect=RuntimeError('provider down')):
            try:
                self.env['govoo.ai.search'].run('query')
                self.fail('Expected a RuntimeError from the patched chat_completion')
            except RuntimeError:
                pass
        request = self.env['govoo.ai.request'].search(
            [('feature', '=', 'ai_f08')], order='id desc', limit=1,
        )
        self.assertEqual(request.status, 'failed')

    def test_run_tolerates_malformed_json_as_no_results(self):
        response = {
            'model': 'gpt-4o-mini',
            'choices': [{'message': {'content': 'not valid json at all'}}],
            'usage': {'total_tokens': 3},
        }
        with self._patch_chat_completion(side_effect=[response]):
            suggestions = self.env['govoo.ai.search'].run('query')
        self.assertFalse(suggestions)
