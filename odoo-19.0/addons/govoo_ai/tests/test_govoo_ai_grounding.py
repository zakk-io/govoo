# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json

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

    def test_schema_catalog_is_cached_on_the_registry(self):
        grounding = self.env['govoo.ai.grounding']
        first = grounding.get_govoo_schema_catalog()
        second = grounding.get_govoo_schema_catalog()
        self.assertEqual(first, second)
        cache_key, cached_catalog = self.env.registry._govoo_ai_schema_cache
        self.assertEqual(cache_key, len(self.env.registry._init_modules))
        self.assertEqual(cached_catalog, first)
