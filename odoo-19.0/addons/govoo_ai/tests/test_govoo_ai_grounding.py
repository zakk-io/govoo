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
