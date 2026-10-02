# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json
import logging

import odoo.modules.module
from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Keeps a conversational Q&A session from growing without bound -- both a
# token-cost control and a sane UX limit. The widget trims its own history
# too, but the backend never trusts a client-supplied list on its own.
MAX_HISTORY_MESSAGES = 12

SYSTEM_PROMPT_TEMPLATE = (
    "You are a governance Q&A assistant speaking to a company's own staff. "
    "Answer their question in a short, clear, conversational narrative (a "
    "few sentences, not a report), grounded ONLY in records you actually "
    "retrieve via the available tools -- never general legal knowledge, "
    "never a plausible-sounding guess (AI-N04). If nothing in the data "
    "available to you supports an answer, say so plainly -- 'not found' "
    "is always a better answer than a wrong one.\n\n"
    "Below is the exact, current list of this deployment's governance "
    "content models and their keyword-searchable fields -- ground truth "
    "for THIS deployment, not a generic guess. Do NOT call list_models or "
    "describe_model for anything in this list; only for something clearly "
    "outside it (e.g. a generic contact or partner).\n\n"
    "Governance content models on this deployment:\n"
    "{schema_catalog}\n\n"
    "Some models have no text field of their own (e.g. a board pack, just "
    "a meeting plus an attachment) -- for those, do a two-step lookup: "
    "find the related model's record first, then filter this model by "
    "its foreign key. Models may also list 'person/party links' (a field "
    "pointing to res.partner or res.users) -- filter those with dot "
    "notation, e.g. [[\"apologies_ids.name\", \"ilike\", \"A Name\"]]. If "
    "the question asks about a specific person's role in a record and no "
    "person/party link field matches that role, you cannot confirm that "
    "fact from unrelated text. For what a meeting discussed or approved, "
    "prefer govoo.agenda.item's short 'title' field over minutes' long "
    "free-text body. Models may also list 'status/type fields' with their "
    "exact stored values (e.g. state (Status): draft, open, passed, "
    "failed) -- a question about status, outcome, or category (open, "
    "overdue, passed, draft, ...) MUST be answered by filtering on that "
    "exact field with one of those exact values, never by filtering on an "
    "unrelated field and assuming the status from context. If a model has "
    "no status/type field listed for the status being asked about, you "
    "cannot confirm it.\n\n"
    "The domain argument is ALWAYS a flat JSON list of 3-element "
    "condition lists [field, operator, value] -- never a string, never a "
    'dict/object like {{"field": {{"ilike": "value"}}}}, and a single '
    "condition is still wrapped in its own outer list: "
    '[["title", "ilike", "value"]] is correct, ["title", "ilike", "value"] '
    'is WRONG. To OR two conditions put "|" as the first element: '
    '["|", ["title", "ilike", "x"], ["text", "ilike", "x"]]. A '
    "search_read result -- success or confirmed-empty -- is final; do not "
    "repeat it with only 'fields'/'limit' changed, and a confirmed-empty "
    "result is a legitimate basis for answering 'not found' rather than "
    "retrying indefinitely.\n\n"
    "When you have an answer, respond with ONLY a JSON object of this "
    'exact shape, no other text: {{"found": true or false, "answer": '
    '"<your short narrative answer, or a brief explanation that it was '
    'not found>", "citations": [{{"model": "<technical model name>", '
    '"res_id": <integer>, "reason": "<one short sentence saying what '
    'this record confirms>"}}]}}. If found is false, citations must be '
    "an empty list. Every sentence of fact in 'answer' must be traceable "
    "to an actual field value you retrieved for a specific cited record "
    "-- never state a fact that is merely topically plausible; a "
    "related-but-unconfirming record means the data does not confirm the "
    "question, not that you should assert it does anyway. Never invent a "
    "model name or record id that a tool did not actually return to you."
)


class GovooAiQa(models.AbstractModel):
    """AI-F09 orchestration: a conversational, grounded Q&A loop built on
    AI-F08's retrieval/citation plumbing (govoo.ai.grounding) -- adding
    narrative synthesis with mandatory citations and an explicit "not
    found" path (AI-N04), the one thing AI-F08 deliberately does not do
    (see govoo_ai_search.py).
    """

    _name = 'govoo.ai.qa'
    _description = 'AI-F09 Governance Q&A Orchestration'

    @api.model
    def run(self, question, history=None):
        """Answer ``question`` and return (answer_text, found, suggestions).

        ``history`` is an optional list of ``{'role': 'user'|'assistant',
        'content': str}`` prior turns, oldest first -- capped at
        MAX_HISTORY_MESSAGES regardless of what the caller supplies.

        :raise UserError: if the question is empty, or no active
            govoo.ai.config has AI-F09 enabled for the current company.
        """
        question = (question or '').strip()
        if not question:
            raise UserError(_('Ask a question first.'))
        config = self.env['govoo.ai.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        if not config or not config.is_feature_enabled('ai_f09'):
            raise UserError(_(
                'Governance Q&A is not enabled for this company. An AI '
                'Administrator must enable AI and tick "AI-F09: '
                'Governance Q&A" in AI > Configuration first.'
            ))
        request = self.env['govoo.ai.request'].create({
            'feature': 'ai_f09',
            'input_summary': question[:500],
        })
        try:
            answer, found, citations, model_name, token_usage = self._run_loop(
                config, question, history or [],
            )
        except Exception:
            request.write({'status': 'failed'})
            # See govoo_ai_search.py::run() for why this commit is needed
            # and why it's skipped under the test harness.
            if not odoo.modules.module.current_test:
                self.env.cr.commit()
            raise
        grounding = self.env['govoo.ai.grounding']
        suggestions = self.env['govoo.ai.suggestion']
        for citation in citations:
            if not grounding.is_match_readable(citation['model'], citation['res_id']):
                # AI-N02, same enforcement as AI-F08: the model's own
                # output is never proof of access.
                _logger.info(
                    'Dropping unreadable AI-F09 citation %s(%s) for user %s',
                    citation['model'], citation['res_id'], self.env.uid,
                )
                continue
            suggestions |= self.env['govoo.ai.suggestion'].create({
                'request_id': request.id,
                'target_model': citation['model'],
                'target_res_id': citation['res_id'],
                'content': citation.get('reason') or '',
                'citations': '%s,%s' % (citation['model'], citation['res_id']),
            })
        request.write({
            'status': 'done',
            'model_name': model_name,
            'token_usage': token_usage,
            'output_ref': (
                'govoo.ai.suggestion,%s' % suggestions[0].id if suggestions else False
            ),
        })
        return answer, found, suggestions

    @api.model
    def run_for_widget(self, question, history=None):
        """RPC-callable wrapper for the chat widget.

        Returns a plain dict -- an OWL component receives this over
        JSON-RPC and can't be handed a recordset.
        """
        answer, found, suggestions = self.run(question, history)
        return {
            'found': found,
            'answer': answer,
            'citations': [
                {
                    'suggestion_id': suggestion.id,
                    'model': suggestion.target_model,
                    'res_id': suggestion.target_res_id,
                    'reason': suggestion.content,
                }
                for suggestion in suggestions
            ],
        }

    @api.model
    def get_widget_config(self):
        """Cheap RPC check the chat widget makes before opening the chat
        panel. Never exposes the api_key or any other config detail --
        only whether AI-F09 is usable right now, and whether the asking
        user could themselves turn it on if not.
        """
        config = self.env['govoo.ai.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        return {
            'configured': bool(config and config.is_feature_enabled('ai_f09')),
            'can_configure': self.env.user.has_group(
                'govoo_ai.group_govoo_ai_administrator',
            ),
        }

    def _run_loop(self, config, question, history):
        """Drive the bounded tool-calling loop and return (answer, found,
        citations, model_name, tokens).

        :raise UserError: if the model does not converge in time (see
            govoo.ai.grounding.run_tool_loop).
        """
        grounding = self.env['govoo.ai.grounding']
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            schema_catalog=grounding.get_govoo_schema_catalog(),
        )
        trimmed_history = [
            {'role': turn.get('role'), 'content': turn.get('content')}
            for turn in history[-MAX_HISTORY_MESSAGES:]
            if turn.get('role') in ('user', 'assistant') and turn.get('content')
        ]
        messages = (
            [{'role': 'system', 'content': system_prompt}]
            + trimmed_history
            + [{'role': 'user', 'content': question}]
        )
        content, model_name, total_tokens = grounding.run_tool_loop(config, messages)
        answer, found, citations = self._parse_answer(content)
        return answer, found, citations, model_name, total_tokens

    def _parse_answer(self, content):
        """Parse the model's final JSON into (answer, found, citations).

        Falls back to a safe "not found" rather than raising on malformed
        output -- same reasoning as AI-F08's _parse_matches: nothing
        unsafe happens either way, and a parsing failure should surface
        as "no grounded answer," not a crash.
        """
        not_found = _('I could not find a grounded answer to that question.')
        try:
            parsed = json.loads(content or '{}')
        except ValueError:
            return not_found, False, []
        if not isinstance(parsed, dict):
            return not_found, False, []
        found = bool(parsed.get('found'))
        answer = parsed.get('answer')
        if not isinstance(answer, str) or not answer.strip():
            return not_found, False, []
        if not found:
            return answer, False, []
        citations_raw = parsed.get('citations')
        citations = [
            citation for citation in citations_raw
            if isinstance(citation, dict)
            and citation.get('model')
            and isinstance(citation.get('res_id'), int)
        ] if isinstance(citations_raw, list) else []
        return answer, found, citations
