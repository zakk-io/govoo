# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.muk_mcp.core.tool import get_tool_index

_logger = logging.getLogger(__name__)

# Shared across every AI-F* feature that grounds itself this way (AI-F08,
# AI-F09, ...): bounds the tool-calling loop so a confused model (or a
# provider outage that keeps returning tool_calls) can't run indefinitely --
# both a cost control and a correctness guard. With the schema catalog given
# directly in each feature's own system prompt, a typical query is one
# search_read call then a final answer; 8 round-trips leaves generous
# headroom for a harder, multi-model query without being unbounded.
DEFAULT_MAX_TOOL_LOOPS = 8

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

    def is_match_readable(self, model_name, res_id):
        """Return whether the current user may read a model's claimed match.

        Shared AI-N02 enforcement point: the model's own JSON output naming
        a model/res_id is never trusted on its own -- this re-checks
        existence and read access exactly as Odoo would for that user
        browsing the UI, for every AI-F* feature that cites source records.
        """
        if model_name not in self.env:
            return False
        record = self.env[model_name].browse(res_id)
        if not record.exists():
            return False
        try:
            record.check_access('read')
        except Exception:
            return False
        return True

    def dispatch_tool_call(self, call):
        """Execute one requested tool call and format it as a tool-role message."""
        name = call['function']['name']
        try:
            arguments = json.loads(call['function'].get('arguments') or '{}')
        except ValueError:
            arguments = {}
        try:
            result = self.call_tool(name, arguments)
        except Exception as exc:
            _logger.info('Grounding tool %s failed: %s', name, exc)
            result = json.dumps({'error': str(exc)})
        return {
            'role': 'tool',
            'tool_call_id': call['id'],
            'content': result if isinstance(result, str) else json.dumps(result, default=str),
        }

    def run_tool_loop(self, config, messages, max_loops=DEFAULT_MAX_TOOL_LOOPS):
        """Drive a bounded OpenAI tool-calling loop against this bridge's
        whitelisted tools and return (final_content, model_name, total_tokens).

        ``messages`` is the full chat-completion message list the caller has
        already built (system prompt, any conversation history, the new
        user turn) -- this method only appends assistant/tool messages as
        the loop progresses. Shared by every AI-F* feature that grounds
        itself this way; each feature supplies its own system prompt and
        interprets ``final_content`` itself (AI-F08 parses a match list,
        AI-F09 parses a narrative answer + citations).

        :raise UserError: if the model does not converge within max_loops.
        """
        client = self.env['govoo.ai.openai.client']
        tools = self.get_tool_schemas()
        model_name = None
        total_tokens = 0
        for _iteration in range(max_loops):
            response = client.chat_completion(
                # sudo(): api_key is restricted to AI Administrators (an AI
                # User must never read the raw secret) but the orchestration
                # itself has to use it, on the user's behalf, to call the
                # provider.
                api_key=config.sudo().api_key,
                messages=messages,
                tools=tools,
            )
            model_name = 'openai:%s' % response.get('model', '')
            total_tokens += (response.get('usage') or {}).get('total_tokens', 0)
            choice = response['choices'][0]['message']
            tool_calls = choice.get('tool_calls')
            if not tool_calls:
                return choice.get('content'), model_name, total_tokens
            messages.append(choice)
            for call in tool_calls:
                messages.append(self.dispatch_tool_call(call))
        raise UserError(_(
            'The AI did not finish in time. Try a more specific question.'
        ))

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
            text_fields = IrField.search([
                ('model_id', '=', model.id),
                ('ttype', 'in', ('char', 'text', 'html')),
                ('store', '=', True),
            ], order='name')
            # Separately surfaced even when the model already has text
            # fields: a person/party link (e.g. govoo.minutes.apologies_ids)
            # is exactly what a "who attended / who was absent / who
            # signed" query needs to actually filter on, instead of the
            # model free-associating an answer from unrelated text it did
            # retrieve (a real hallucination seen in live testing --
            # confidently claiming a named person's attendance status from
            # a record that never mentions them).
            party_fields = IrField.search([
                ('model_id', '=', model.id),
                ('ttype', 'in', ('many2one', 'many2many', 'one2many')),
                ('relation', 'in', ('res.partner', 'res.users')),
                ('store', '=', True),
            ], order='name')
            # Also always surfaced: Selection fields (state, result, type,
            # ...). Without this, a status/outcome question (e.g. "which
            # resolutions are still open") has no field to filter on at
            # all -- a real failure seen in live testing where the model,
            # lacking any field for "open", filtered on an unrelated one
            # (access_token) instead, effectively retrieved an unfiltered
            # set, and then asserted statuses it never actually checked.
            # The exact stored values are listed (not just labels) since
            # those are what a domain filter must match literally.
            selection_fields = IrField.search([
                ('model_id', '=', model.id),
                ('ttype', '=', 'selection'),
                ('store', '=', True),
            ], order='name')
            # Also always surfaced: Date/Datetime fields. A label like
            # "period" on govoo.compliance.instance is the month an
            # obligation *covers* (e.g. "2026-09" for a return filed in
            # October), not the month it's *due* -- without an explicit
            # due_date field listed, a "due this month" question has no
            # way to tell those apart and silently filters on the wrong
            # one (a real failure seen in live testing).
            date_fields = IrField.search([
                ('model_id', '=', model.id),
                ('ttype', 'in', ('date', 'datetime')),
                ('store', '=', True),
            ], order='name')
            if text_fields:
                field_list = ', '.join(
                    '%s (%s)' % (field.name, field.field_description)
                    for field in text_fields
                )
                line = '- %s [%s]: %s' % (model.model, model.name, field_list)
                if party_fields:
                    party_list = ', '.join(
                        '%s -> %s' % (field.name, field.relation)
                        for field in party_fields
                    )
                    line += '; person/party links: %s' % party_list
                status_list = self._format_selection_fields(model.model, selection_fields)
                if status_list:
                    line += '; status/type fields: %s' % status_list
                if date_fields:
                    date_list = ', '.join(
                        '%s (%s)' % (field.name, field.field_description)
                        for field in date_fields
                    )
                    line += '; date fields: %s' % date_list
                lines.append(line)
                continue
            # A model with no keyword-searchable field of its own (e.g. a
            # board pack, which is just a meeting + an attachment) is
            # otherwise invisible here, and the model has no way to guess
            # it needs to look it up through a related model instead of
            # concluding it does not exist. List its many2one links so a
            # query about it can be answered as a two-step lookup: find
            # the related record's id first, then filter this model by
            # that foreign key.
            relations = IrField.search([
                ('model_id', '=', model.id),
                ('ttype', '=', 'many2one'),
                ('store', '=', True),
            ], order='name')
            if not relations:
                continue
            relation_list = ', '.join(
                '%s -> %s' % (field.name, field.relation)
                for field in relations
            )
            line = (
                '- %s [%s]: (no text field of its own; look up via a '
                'related model first, then filter by its foreign key) %s'
                % (model.model, model.name, relation_list)
            )
            status_list = self._format_selection_fields(model.model, selection_fields)
            if status_list:
                line += '; status/type fields: %s' % status_list
            lines.append(line)
        return '\n'.join(lines)

    def _format_selection_fields(self, model_name, selection_fields):
        """Render Selection fields as 'name (Label): value1, value2, ...',
        using the literal stored values a domain filter must match -- not
        just their human-readable labels.

        Resolves options through the live ORM field's own
        _description_selection(), not ir.model.fields.selection directly:
        for a `related=` Selection field (e.g.
        govoo.register.director.role, related to
        govoo.appointment.role), Odoo leaves ir.model.fields.selection as
        an empty '[]' on the related model's own field row -- the literal
        list only ever lives on the source field. Reading it straight off
        ir.model.fields silently produced a model with no status/type
        fields in the catalog at all, which is exactly what let the AI
        earlier conflate the Company Secretary (role='secretary') with
        the actual directors when asked "who are our current directors,"
        since it had no field value to tell the two roles apart.
        _description_selection() is what Odoo itself calls to resolve a
        field's selection for the UI, so it works the same for related
        and computed Selection fields as for a plain static list.
        """
        parts = []
        model_fields = self.env[model_name]._fields
        for field in selection_fields:
            live_field = model_fields.get(field.name)
            if live_field is None:
                continue
            try:
                options = live_field._description_selection(self.env)
            except Exception:
                continue
            if not options:
                continue
            values = ', '.join(str(value) for value, _label in options)
            parts.append('%s (%s): %s' % (field.name, field.field_description, values))
        return '; '.join(parts)
