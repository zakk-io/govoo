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

    def get_govoo_schema_catalog(self):
        """Return a compact, deterministic map of every installed 'govoo.*'
        content model and its keyword-searchable (char/text/html) fields.

        Without this, AI-F08's tool-calling loop spent most of its budget
        calling list_models (which returns every installed model, custom
        and standard Odoo alike -- hundreds of entries) and then
        describe_model per guessed candidate, just to rediscover this same
        static shape on every single query. That repeated discovery dance
        was the main cause of hitting MAX_TOOL_LOOPS before reaching a
        final answer (see issue #216 live-testing notes). This is computed
        directly from ir.model/ir.model.fields -- a few dozen rows of
        schema metadata, not row data, hence .sudo() -- and is injected
        straight into the system prompt, so a typical query now needs one
        search_read call instead of several rounds of guessing.

        list_models/describe_model remain available as tools for anything
        outside the 'govoo.*' namespace (e.g. res.partner).

        Cached on the registry, keyed by its installed-module count --
        the same invalidation pattern muk_mcp's own get_tool_index uses
        (core/tool.py) -- so a module install/upgrade rebuilds it but a
        plain search doesn't re-run this on every single request.
        """
        registry = self.env.registry
        cache_key = len(registry._init_modules)
        cached = getattr(registry, '_govoo_ai_schema_cache', None)
        if cached is not None and cached[0] == cache_key:
            return cached[1]
        catalog = self._build_govoo_schema_catalog()
        registry._govoo_ai_schema_cache = (cache_key, catalog)
        return catalog

    def _build_govoo_schema_catalog(self):
        """Compute the schema catalog fresh (see get_govoo_schema_catalog)."""
        IrModel = self.env['ir.model'].sudo()
        IrField = self.env['ir.model.fields'].sudo()
        content_models = IrModel.search([
            ('model', 'like', 'govoo.%'),
            ('model', 'not like', 'govoo.ai.%'),
            ('transient', '=', False),
        ], order='model')
        lines = []
        for model in content_models:
            fields = IrField.search([
                ('model_id', '=', model.id),
                ('ttype', 'in', ('char', 'text', 'html')),
                ('store', '=', True),
            ], order='name')
            if not fields:
                continue
            field_list = ', '.join(
                '%s (%s)' % (field.name, field.field_description)
                for field in fields
            )
            lines.append('- %s [%s]: %s' % (model.model, model.name, field_list))
        return '\n'.join(lines)
