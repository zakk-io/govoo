# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.muk_mcp.core.tool import get_tool_index

# Issue #216: the only muk_mcp tools ever handed to a model or executed on
# its behalf. All six are category='read' in muk_mcp itself (verified
# against mcp/read.py and mcp/introspect.py, not assumed) -- muk_mcp's own
# write tools (create_records/update_records/delete_records/call_method)
# are never reachable from here. That boundary is what keeps this feature
# from becoming a way for the model to mutate governance data outside the
# govoo.ai.suggestion human-review path (AI-N03).
WHITELISTED_TOOLS = (
    'search_read',
    'read_records',
    'search_count',
    'read_group',
    'describe_model',
    'list_models',
)


class GovooAiGrounding(models.AbstractModel):
    """Bridge from govoo_ai's own AI-F* features to muk_mcp's existing,
    permission-aware, audited read-tool surface -- reused rather than
    rebuilt (see issue #216's design discussion). Every call runs under the
    calling user's own `self.env`, so Odoo's record rules apply exactly as
    they would for that user browsing the UI (AI-N02); `enforce_scope='read'`
    is a second, code-level guarantee against write tools that holds even
    if a prompt-injected query somehow talked the model into asking for one.
    """

    _name = 'govoo.ai.grounding'
    _description = 'AI Grounding Bridge (read-only muk_mcp tools)'

    def get_tool_schemas(self):
        """Return the whitelisted tools as OpenAI chat-completion tool specs."""
        index = get_tool_index(self.env)
        schemas = []
        for name in WHITELISTED_TOOLS:
            entry = index.get(name)
            if not entry:
                continue
            schemas.append({
                'type': 'function',
                'function': {
                    'name': name,
                    'description': entry['description'],
                    'parameters': entry['input_schema'],
                },
            })
        return schemas

    def call_tool(self, name, arguments):
        """Execute a whitelisted, read-only muk_mcp tool and return its result.

        :raise UserError: if ``name`` is not one of the whitelisted tools.
        """
        if name not in WHITELISTED_TOOLS:
            raise UserError(_(
                'Tool "%s" is not permitted for AI grounding.'
            ) % name)
        text, _info = self.env['muk_mcp.tool']._call(
            name, arguments, self.env, enforce_scope='read',
        )
        return text
