# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Bounds the tool-calling loop so a confused model (or a provider outage
# that keeps returning tool_calls) can't run indefinitely -- both a cost
# control and a correctness guard. Five round-trips is generous for a
# search across a handful of governance models.
MAX_TOOL_LOOPS = 5

SYSTEM_PROMPT = (
    "You are a search assistant for a corporate governance system. Use the "
    "available tools to find records matching the user's query across "
    "governance data (resolutions, minutes, registers, compliance "
    "instances, contracts, policies -- whichever models are actually "
    "installed). Do not write a narrative answer or synthesize information "
    "across records -- that is a different feature. When you have found "
    "the relevant records, respond with ONLY a JSON object of this exact "
    'shape, no other text: {"matches": [{"model": "<technical model '
    'name>", "res_id": <integer>, "reason": "<one short sentence saying '
    'why this record matched>"}]}. If nothing matches, respond with '
    '{"matches": []}. Never invent a model name or record id that a tool '
    "did not actually return to you."
)


class GovooAiSearch(models.AbstractModel):
    """AI-F08 orchestration: runs the bounded tool-calling loop against the
    grounding bridge and turns the model's structured result into
    govoo.ai.suggestion records, one per matched source record -- never a
    single synthesized narrative (that's AI-F09, a separate issue reusing
    this same loop)."""

    _name = 'govoo.ai.search'
    _description = 'AI-F08 Semantic Search Orchestration'

    def run(self, query):
        """Run a semantic search for ``query`` and return the resulting suggestions.

        :raise UserError: if no active `govoo.ai.config` exists for the
            current company, or the feature is not enabled on it.
        """
        query = (query or '').strip()
        if not query:
            raise UserError(_('Enter a question or search term first.'))
        config = self.env['govoo.ai.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        if not config or not config.is_feature_enabled('ai_f08'):
            raise UserError(_(
                'Semantic Search is not enabled for this company. An AI '
                'Administrator must enable AI and tick "AI-F08: Semantic '
                'Search (RAG)" in AI > Configuration first.'
            ))
        request = self.env['govoo.ai.request'].create({
            'feature': 'ai_f08',
            'input_summary': query[:500],
        })
        try:
            matches, model_name, token_usage = self._run_loop(config, query)
        except Exception:
            request.write({'status': 'failed'})
            raise
        suggestions = self.env['govoo.ai.suggestion']
        for match in matches:
            if not self._match_is_readable(match['model'], match['res_id']):
                # AI-N02: the model's own JSON output is not proof of
                # access. A hallucinated or out-of-scope model/res_id pair
                # is silently dropped rather than surfaced -- this is the
                # actual enforcement point, not just an instruction in the
                # system prompt.
                _logger.info(
                    'Dropping unreadable AI-F08 match %s(%s) for user %s',
                    match['model'], match['res_id'], self.env.uid,
                )
                continue
            suggestions |= self.env['govoo.ai.suggestion'].create({
                'request_id': request.id,
                'target_model': match['model'],
                'target_res_id': match['res_id'],
                'content': match.get('reason') or '',
                'citations': '%s,%s' % (match['model'], match['res_id']),
            })
        request.write({
            'status': 'done',
            'model_name': model_name,
            'token_usage': token_usage,
            'output_ref': (
                'govoo.ai.suggestion,%s' % suggestions[0].id if suggestions else False
            ),
        })
        return suggestions

    def _match_is_readable(self, model_name, res_id):
        """Return whether the current user may read the claimed match.

        The model's own JSON output naming a model/res_id is never trusted
        on its own -- this re-checks existence and read access exactly as
        Odoo would for that user browsing the UI (AI-N02).
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

    def _run_loop(self, config, query):
        """Drive the bounded tool-calling loop and return (matches, model_name, tokens).

        :raise UserError: if the model does not converge within
            MAX_TOOL_LOOPS round-trips.
        """
        grounding = self.env['govoo.ai.grounding']
        client = self.env['govoo.ai.openai.client']
        tools = grounding.get_tool_schemas()
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': query},
        ]
        model_name = None
        total_tokens = 0
        for _iteration in range(MAX_TOOL_LOOPS):
            response = client.chat_completion(
                api_key=config.api_key,
                messages=messages,
                tools=tools,
            )
            model_name = 'openai:%s' % response.get('model', '')
            total_tokens += (response.get('usage') or {}).get('total_tokens', 0)
            choice = response['choices'][0]['message']
            tool_calls = choice.get('tool_calls')
            if not tool_calls:
                return (
                    self._parse_matches(choice.get('content')),
                    model_name,
                    total_tokens,
                )
            messages.append(choice)
            for call in tool_calls:
                messages.append(self._dispatch_tool_call(grounding, call))
        raise UserError(_(
            'The AI search did not finish in time. Try a more specific query.'
        ))

    def _dispatch_tool_call(self, grounding, call):
        """Execute one requested tool call and format it as a tool-role message."""
        name = call['function']['name']
        try:
            arguments = json.loads(call['function'].get('arguments') or '{}')
        except ValueError:
            arguments = {}
        try:
            result = grounding.call_tool(name, arguments)
        except Exception as exc:
            _logger.info('Grounding tool %s failed: %s', name, exc)
            result = json.dumps({'error': str(exc)})
        return {
            'role': 'tool',
            'tool_call_id': call['id'],
            'content': result if isinstance(result, str) else json.dumps(result, default=str),
        }

    def _parse_matches(self, content):
        """Parse the model's final JSON content into a list of match dicts.

        Silently returns an empty list on malformed output rather than
        raising -- a model that fails to follow the JSON contract should
        surface as "no results," not an error, since nothing unsafe
        happens either way (no suggestion is created for a match that
        doesn't parse).
        """
        try:
            parsed = json.loads(content or '{}')
        except ValueError:
            return []
        matches = parsed.get('matches') if isinstance(parsed, dict) else None
        if not isinstance(matches, list):
            return []
        return [
            match for match in matches
            if isinstance(match, dict)
            and match.get('model')
            and isinstance(match.get('res_id'), int)
        ]
