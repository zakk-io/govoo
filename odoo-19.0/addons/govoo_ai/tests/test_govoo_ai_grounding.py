# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import GovooAiTestBase


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiGrounding(GovooAiTestBase):

    def test_get_tool_schemas_only_whitelisted(self):
        schemas = self.env['govoo.ai.grounding'].get_tool_schemas()
        names = {entry['function']['name'] for entry in schemas}
        self.assertIn('search_read', names)
        self.assertIn('search_count', names)
        self.assertNotIn('create_records', names)
        self.assertNotIn('update_records', names)
        self.assertNotIn('delete_records', names)
        self.assertNotIn('call_method', names)

    def test_call_tool_rejects_non_whitelisted_name(self):
        with self.assertRaises(UserError):
            self.env['govoo.ai.grounding'].call_tool('create_records', {
                'model': 'res.partner', 'values': {'name': 'x'},
            })

    def test_call_tool_runs_a_real_whitelisted_tool(self):
        # muk_mcp serializes a method tool's dict return to a JSON string
        # (core/tool.py::_serialize_result) -- parse it back rather than
        # asserting on the raw string.
        result = self.env['govoo.ai.grounding'].call_tool('search_count', {
            'model': 'res.partner',
            'domain': [],
        })
        parsed = json.loads(result)
        self.assertIn('count', parsed)
        self.assertIsInstance(parsed['count'], int)

    def test_schema_catalog_excludes_ai_infrastructure_and_wizards(self):
        # govoo_ai's own models (config/request/suggestion/search/wizard)
        # are always installed here, so this is a reliable negative check
        # regardless of which other govoo_* modules are in this test run.
        catalog = self.env['govoo.ai.grounding'].get_govoo_schema_catalog()
        self.assertNotIn('govoo.ai.', catalog)

    def test_schema_catalog_includes_resolution_title_field_if_installed(self):
        if 'govoo.resolution' not in self.env:
            self.skipTest('govoo_board is not installed in this test run')
        catalog = self.env['govoo.ai.grounding'].get_govoo_schema_catalog()
        self.assertIn('govoo.resolution', catalog)
        self.assertIn('title', catalog)

    def test_schema_catalog_lists_relation_only_models_via_their_fk(self):
        if 'govoo.board.pack' not in self.env:
            self.skipTest('govoo_board is not installed in this test run')
        catalog = self.env['govoo.ai.grounding'].get_govoo_schema_catalog()
        self.assertIn('govoo.board.pack', catalog)
        self.assertIn('meeting_id -> govoo.meeting', catalog)

    def test_schema_catalog_lists_person_party_links_alongside_text_fields(self):
        if 'govoo.minutes' not in self.env:
            self.skipTest('govoo_board is not installed in this test run')
        catalog = self.env['govoo.ai.grounding'].get_govoo_schema_catalog()
        self.assertIn('govoo.minutes', catalog)
        self.assertIn('apologies_ids -> res.partner', catalog)
        self.assertIn('attendance_ids -> res.partner', catalog)

    def test_schema_catalog_lists_selection_field_values(self):
        if 'govoo.resolution' not in self.env:
            self.skipTest('govoo_board is not installed in this test run')
        catalog = self.env['govoo.ai.grounding'].get_govoo_schema_catalog()
        self.assertIn('govoo.resolution', catalog)
        self.assertIn('status/type fields', catalog)
        self.assertIn('state (Status): draft, open, passed, failed, withdrawn', catalog)

    def test_schema_catalog_lists_selection_values_for_a_related_selection_field(self):
        # Regression: govoo.register.director.role/state are `related=`
        # Selection fields (pulled from govoo.appointment) -- Odoo leaves
        # ir.model.fields.selection as the literal string '[]' on the
        # related model's own field row, so a naive ast.literal_eval of
        # that column found nothing and silently dropped role/state from
        # the catalog entirely. That gap let the AI conflate the Company
        # Secretary (role='secretary') with an actual director when asked
        # "who are our current directors" (live-testing finding).
        if 'govoo.register.director' not in self.env:
            self.skipTest('govoo_secretarial is not installed in this test run')
        catalog = self.env['govoo.ai.grounding'].get_govoo_schema_catalog()
        self.assertIn('govoo.register.director', catalog)
        self.assertIn('status/type fields', catalog)
        self.assertIn(
            'role (Role): director, secretary, chair, md, committee_member', catalog,
        )
        self.assertIn('state (Status): active, resigned', catalog)

    def test_schema_catalog_lists_date_fields_alongside_text_fields(self):
        if 'govoo.compliance.instance' not in self.env:
            self.skipTest('govoo_compliance is not installed in this test run')
        catalog = self.env['govoo.ai.grounding'].get_govoo_schema_catalog()
        self.assertIn('govoo.compliance.instance', catalog)
        self.assertIn('date fields', catalog)
        self.assertIn('due_date (Due Date)', catalog)

    def test_schema_catalog_is_cached_on_the_registry(self):
        grounding = self.env['govoo.ai.grounding']
        first = grounding.get_govoo_schema_catalog()
        second = grounding.get_govoo_schema_catalog()
        self.assertEqual(first, second)
        cache_key, cached_catalog = self.env.registry._govoo_ai_schema_cache
        self.assertEqual(cache_key, len(self.env.registry._init_modules))
        self.assertEqual(cached_catalog, first)

    def test_is_match_readable_true_for_an_existing_readable_record(self):
        partner = self.env['res.partner'].create({'name': 'Findable'})
        self.assertTrue(
            self.env['govoo.ai.grounding'].is_match_readable('res.partner', partner.id)
        )

    def test_is_match_readable_false_for_unknown_model(self):
        self.assertFalse(
            self.env['govoo.ai.grounding'].is_match_readable('not.a.real.model', 1)
        )

    def test_is_match_readable_false_for_nonexistent_id(self):
        self.assertFalse(
            self.env['govoo.ai.grounding'].is_match_readable('res.partner', 999999999)
        )

    def test_dispatch_tool_call_runs_a_whitelisted_tool(self):
        call = {
            'id': 'call_1',
            'function': {
                'name': 'search_count',
                'arguments': json.dumps({'model': 'res.partner', 'domain': []}),
            },
        }
        message = self.env['govoo.ai.grounding'].dispatch_tool_call(call)
        self.assertEqual(message['role'], 'tool')
        self.assertEqual(message['tool_call_id'], 'call_1')
        self.assertIn('count', json.loads(message['content']))

    def test_dispatch_tool_call_reports_a_failure_as_tool_content_not_an_exception(self):
        call = {'id': 'call_2', 'function': {'name': 'create_records', 'arguments': '{}'}}
        message = self.env['govoo.ai.grounding'].dispatch_tool_call(call)
        self.assertIn('error', json.loads(message['content']))

    def test_run_tool_loop_returns_final_content_once_there_are_no_tool_calls(self):
        config = self._make_active_config()
        response = {
            'model': 'gpt-4o-mini',
            'choices': [{'message': {'content': 'final answer'}}],
            'usage': {'total_tokens': 7},
        }
        with mock.patch.object(
            type(self.env['govoo.ai.openai.client']), 'chat_completion', side_effect=[response],
        ):
            content, model_name, tokens = self.env['govoo.ai.grounding'].run_tool_loop(
                config, [{'role': 'system', 'content': 'x'}, {'role': 'user', 'content': 'y'}],
            )
        self.assertEqual(content, 'final answer')
        self.assertEqual(model_name, 'openai:gpt-4o-mini')
        self.assertEqual(tokens, 7)

    def test_run_tool_loop_raises_when_it_never_converges(self):
        config = self._make_active_config()
        tool_call_response = {
            'model': 'gpt-4o-mini',
            'choices': [{'message': {'tool_calls': [{
                'id': 'c1',
                'function': {
                    'name': 'search_count',
                    'arguments': json.dumps({'model': 'res.partner', 'domain': []}),
                },
            }]}}],
            'usage': {'total_tokens': 1},
        }
        with mock.patch.object(
            type(self.env['govoo.ai.openai.client']), 'chat_completion',
            side_effect=lambda **kw: tool_call_response,
        ):
            with self.assertRaises(UserError):
                self.env['govoo.ai.grounding'].run_tool_loop(
                    config,
                    [{'role': 'system', 'content': 'x'}, {'role': 'user', 'content': 'y'}],
                    max_loops=2,
                )
