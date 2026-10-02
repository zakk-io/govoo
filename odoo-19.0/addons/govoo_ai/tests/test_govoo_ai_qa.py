# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models.govoo_ai_qa import MAX_HISTORY_MESSAGES
from .common import GovooAiTestBase


def _final_response(found, answer, citations=None, tokens=10):
    return {
        'model': 'gpt-4o-mini',
        'choices': [{'message': {
            'role': 'assistant',
            'content': json.dumps({
                'found': found,
                'answer': answer,
                'citations': citations or [],
            }),
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
class TestGovooAiQa(GovooAiTestBase):

    def setUp(self):
        super().setUp()
        self._make_active_config(cap=100000, enabled_features=('ai_f09',))
        self.target = self.env['res.partner'].create({'name': 'Findable Partner'})

    def _patch_chat_completion(self, side_effect):
        return mock.patch.object(
            type(self.env['govoo.ai.openai.client']),
            'chat_completion',
            side_effect=side_effect,
        )

    def test_run_raises_when_feature_not_enabled(self):
        self.env['govoo.ai.config'].search([]).write({'ai_f09': False})
        with self.assertRaises(UserError):
            self.env['govoo.ai.qa'].run('anything')

    def test_run_raises_on_empty_question(self):
        with self.assertRaises(UserError):
            self.env['govoo.ai.qa'].run('   ')

    def test_run_returns_grounded_answer_with_citation(self):
        response = _final_response(
            True,
            'Findable Partner is on file.',
            citations=[{'model': 'res.partner', 'res_id': self.target.id, 'reason': 'Name matches.'}],
        )
        with self._patch_chat_completion(side_effect=[response]):
            answer, found, suggestions = self.env['govoo.ai.qa'].run('Who is Findable Partner?')
        self.assertTrue(found)
        self.assertEqual(answer, 'Findable Partner is on file.')
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions.target_model, 'res.partner')
        self.assertEqual(suggestions.target_res_id, self.target.id)
        self.assertEqual(suggestions.request_id.feature, 'ai_f09')
        self.assertEqual(suggestions.request_id.status, 'done')

    def test_run_reports_not_found_without_fabricating_citations(self):
        response = _final_response(False, 'That is not in the data available to me.')
        with self._patch_chat_completion(side_effect=[response]):
            answer, found, suggestions = self.env['govoo.ai.qa'].run('question')
        self.assertFalse(found)
        self.assertEqual(answer, 'That is not in the data available to me.')
        self.assertFalse(suggestions)

    def test_run_drops_citation_for_nonexistent_record(self):
        response = _final_response(
            True, 'answer',
            citations=[{'model': 'res.partner', 'res_id': 999999999, 'reason': 'hallucinated'}],
        )
        with self._patch_chat_completion(side_effect=[response]):
            _answer, found, suggestions = self.env['govoo.ai.qa'].run('question')
        self.assertTrue(found)
        self.assertFalse(suggestions)

    def test_run_drops_citation_for_unknown_model(self):
        response = _final_response(
            True, 'answer',
            citations=[{'model': 'not.a.real.model', 'res_id': 1, 'reason': 'hallucinated'}],
        )
        with self._patch_chat_completion(side_effect=[response]):
            _answer, _found, suggestions = self.env['govoo.ai.qa'].run('question')
        self.assertFalse(suggestions)

    def test_run_ignores_citations_when_found_is_false(self):
        # A model claiming found=false but still listing citations is
        # contradictory output -- citations are only ever trusted when the
        # model itself says the question was answered.
        response = _final_response(
            False, 'not found',
            citations=[{'model': 'res.partner', 'res_id': self.target.id, 'reason': 'x'}],
        )
        with self._patch_chat_completion(side_effect=[response]):
            _answer, found, suggestions = self.env['govoo.ai.qa'].run('question')
        self.assertFalse(found)
        self.assertFalse(suggestions)

    def test_run_dispatches_tool_call_before_final_answer(self):
        responses = [
            _tool_call_response(),
            _final_response(
                True, 'Found via search_count.',
                citations=[{'model': 'res.partner', 'res_id': self.target.id, 'reason': 'x'}],
            ),
        ]
        with self._patch_chat_completion(side_effect=responses):
            _answer, found, suggestions = self.env['govoo.ai.qa'].run('question')
        self.assertTrue(found)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions.request_id.token_usage, 15)  # 5 + 10

    def test_run_raises_when_loop_does_not_converge(self):
        with self._patch_chat_completion(side_effect=lambda **kw: _tool_call_response()):
            with self.assertRaises(UserError):
                self.env['govoo.ai.qa'].run('question')

    def test_request_marked_failed_on_error(self):
        # See test_govoo_ai_search.py's identical test for why
        # self.assertRaises is deliberately not used here.
        with self._patch_chat_completion(side_effect=RuntimeError('provider down')):
            try:
                self.env['govoo.ai.qa'].run('question')
                self.fail('Expected a RuntimeError from the patched chat_completion')
            except RuntimeError:
                pass
        request = self.env['govoo.ai.request'].search(
            [('feature', '=', 'ai_f09')], order='id desc', limit=1,
        )
        self.assertEqual(request.status, 'failed')

    def test_run_tolerates_malformed_json_as_not_found(self):
        response = {
            'model': 'gpt-4o-mini',
            'choices': [{'message': {'content': 'not valid json at all'}}],
            'usage': {'total_tokens': 3},
        }
        with self._patch_chat_completion(side_effect=[response]):
            answer, found, suggestions = self.env['govoo.ai.qa'].run('question')
        self.assertFalse(found)
        self.assertFalse(suggestions)
        self.assertTrue(answer)

    def test_history_is_passed_to_the_model_and_trimmed(self):
        long_history = [
            {'role': 'user' if i % 2 == 0 else 'assistant', 'content': 'turn %s' % i}
            for i in range(30)
        ]
        captured = {}

        def _capture(**kwargs):
            captured['messages'] = kwargs['messages']
            return _final_response(False, 'not found')

        with self._patch_chat_completion(side_effect=_capture):
            self.env['govoo.ai.qa'].run('question', history=long_history)
        # system prompt + trimmed history + new user turn
        self.assertEqual(len(captured['messages']), 1 + MAX_HISTORY_MESSAGES + 1)
        self.assertEqual(captured['messages'][-1], {'role': 'user', 'content': 'question'})

    def test_run_for_widget_returns_a_plain_dict(self):
        response = _final_response(
            True, 'Found it.',
            citations=[{'model': 'res.partner', 'res_id': self.target.id, 'reason': 'match'}],
        )
        with self._patch_chat_completion(side_effect=[response]):
            result = self.env['govoo.ai.qa'].run_for_widget('question')
        self.assertTrue(result['found'])
        self.assertEqual(result['answer'], 'Found it.')
        self.assertEqual(len(result['citations']), 1)
        self.assertEqual(result['citations'][0]['model'], 'res.partner')
        self.assertEqual(result['citations'][0]['res_id'], self.target.id)
        self.assertIn('suggestion_id', result['citations'][0])

    def test_get_widget_config_reports_enabled_state(self):
        result = self.env['govoo.ai.qa'].get_widget_config()
        self.assertTrue(result['configured'])
        self.assertIn('can_configure', result)

    def test_get_widget_config_reports_disabled_when_feature_off(self):
        self.env['govoo.ai.config'].search([]).write({'ai_f09': False})
        result = self.env['govoo.ai.qa'].get_widget_config()
        self.assertFalse(result['configured'])
