# Part of Govoo. See LICENSE file for full copyright and licensing details.

import json
import logging

import odoo.modules.module
from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = (
    "You are a search assistant for a corporate governance system. Use the "
    "available tools to find records matching the user's query. Below is "
    "the exact, current list of this deployment's governance content "
    "models and their keyword-searchable fields -- this is ground truth "
    "for THIS deployment, not a generic guess, so go straight to "
    "search_read on the right model using these exact field names. Do "
    "NOT call list_models or describe_model for anything in this list -- "
    "that was the main cause of past searches running out of time, "
    "because list_models returns every installed model (Odoo core and "
    "custom alike, often hundreds) sorted alphabetically, so 'govoo.*' "
    "content models frequently would not even appear in its default "
    "results. Only call list_models/describe_model if the query is "
    "clearly about something NOT in this list (e.g. a generic contact "
    "or partner).\n\n"
    "Governance content models on this deployment:\n"
    "{schema_catalog}\n\n"
    "Some models above are marked as having no text field of their own "
    "(e.g. a board pack, which is just a meeting plus an attachment). For "
    "those, do a two-step lookup: first search_read the related model "
    "named after the '->' (e.g. govoo.meeting) by its own text field to "
    "get its id, then search_read the original model filtered by its "
    "foreign key equal to that id, e.g. domain = [[\"meeting_id\", \"=\", "
    "42]]. This is normal and expected, not a sign the record does not "
    "exist. Models may also list 'person/party links' (a field name "
    "pointing to res.partner or res.users) -- to filter by a named "
    "person on one of those fields, use dot notation directly in the "
    "domain: [[\"apologies_ids.name\", \"ilike\", \"Robert Nkurunziza\"]]. "
    "If the query asks about a specific person's role in a record (e.g. "
    "attended, was absent, signed, approved) and the model has no "
    "person/party link field that matches that role, you cannot confirm "
    "that fact -- do not guess at it from unrelated text. For a query "
    "about what a meeting discussed, covered, or approved, prefer "
    "govoo.agenda.item's short 'title' field first -- it names the exact "
    "topic for a specific meeting -- rather than searching the long "
    "free-text body of govoo.minutes, which is harder to match reliably "
    "and only needed if no agenda item covers the topic. Models may also "
    "list 'status/type fields' with their exact stored values (e.g. state "
    "(Status): draft, open, passed, failed) -- a query about status, "
    "outcome, or category (open, overdue, passed, draft, ...) MUST filter "
    "on that exact field with one of those exact values, never on an "
    "unrelated field. If a model has no status/type field for the status "
    "being asked about, you cannot confirm it.\n\n"
    "When you filter by a keyword or phrase, put every short "
    "title/name-like field into the same OR condition as any long "
    "text/body/description field on that model -- a phrase like 'Articles "
    "of Association' is much more likely to appear in a short title field "
    "than deep in a long text field, so never filter on only the long "
    "field. The domain argument is ALWAYS a flat JSON list of 3-element "
    "condition lists [field, operator, value] -- it is NEVER a string, "
    'and NEVER a dict/object like {{"field": {{"ilike": "value"}}}} (that is '
    "not valid Odoo domain syntax and will always fail). To OR two "
    "conditions, put the literal string \"|\" as the FIRST element of "
    "that same flat list, immediately followed by the two condition "
    "lists -- for example, to match title OR text on \"credit facility\": "
    'domain = ["|", ["title", "ilike", "credit facility"], ["text", '
    '"ilike", "credit facility"]]. That is 3 elements in one list: the '
    '"|" string, then each condition as its own 3-item list. For a '
    'single condition with no OR, domain is ALWAYS still a list '
    'containing that one 3-item list -- never the bare condition by '
    'itself: domain = [["title", "ilike", "credit facility"]] is correct, '
    'domain = ["title", "ilike", "credit facility"] is WRONG and will '
    "always fail, on ANY field including dot-notation ones like "
    '"apologies_ids.name". Before every search_read call, check that '
    "domain is a list whose items are themselves lists (or the strings "
    '"|"/"&"). STOP after the first search_read result for a given '
    "model+domain, success or empty -- do not call it again with only "
    "'fields' or 'limit' changed, and do not retry a call that just "
    "failed with the exact same domain. A confirmed empty result IS a "
    'complete answer: either try a genuinely different domain/model, or '
    'answer {{"matches": []}} right away. Likewise, a non-empty result '
    "is also immediately usable -- this feature returns a LIST of "
    "matches, so if a search_read already found one or more genuinely "
    "relevant records, include them in the final answer rather than "
    "continuing to search for a single 'best' one; do not keep narrowing "
    "down once you have confirmed matches in hand. If a model "
    "returns no results after one or two keyword variations, that model "
    "is probably the wrong one -- move on to a different candidate model "
    "from the list above instead of retrying more synonyms on the same "
    "model; a decision to amend a governance document is normally "
    "recorded as a resolution/minutes entry, not as a copy of the "
    "document itself. Never guess a technical model or field name that "
    "was not actually given to you above or returned by a tool. Do not "
    "write a "
    "narrative answer or synthesize information across records -- that is "
    "a different feature. When you have found the relevant records, "
    'respond with ONLY a JSON object of this exact shape, no other text: '
    '{{"matches": [{{"model": "<technical model name>", "res_id": '
    '<integer>, "reason": "<one short sentence saying why this record '
    'matched>"}}]}}. If nothing matches, respond with {{"matches": []}}. '
    "Never invent a model name or record id that a tool did not actually "
    "return to you. The 'reason' is held to the same standard: it must "
    "describe only a fact you can point to in an actual field value a "
    "tool returned for that exact record (e.g. its title contains the "
    "phrase, or its apologies_ids actually includes that person's name) "
    "-- never a specific claim (who did what, an outcome, a date, an "
    "amount) that you inferred, assumed, or generalized from a different "
    "record or from the model's general subject matter. A record that is "
    "merely topically related but does not confirm the exact fact the "
    "user asked about is not a match -- leave it out rather than write a "
    "reason that overstates what was actually retrieved."
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
            # The re-raise below will otherwise take the whole transaction
            # down with it (Odoo's HTTP dispatch rolls back on any uncaught
            # exception), silently losing this audit-trail row. Commit it
            # now so a failed request is never invisible after the fact.
            # Skipped under the test harness: TransactionCase forbids a
            # direct commit/rollback on its own savepoint-backed cursor,
            # and tests never go through the real HTTP dispatch rollback
            # this guards against.
            if not odoo.modules.module.current_test:
                self.env.cr.commit()
            raise
        grounding = self.env['govoo.ai.grounding']
        suggestions = self.env['govoo.ai.suggestion']
        for match in matches:
            if not grounding.is_match_readable(match['model'], match['res_id']):
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

    def _run_loop(self, config, query):
        """Drive the bounded tool-calling loop and return (matches, model_name, tokens).

        :raise UserError: if the model does not converge in time (see
            govoo.ai.grounding.run_tool_loop).
        """
        grounding = self.env['govoo.ai.grounding']
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            schema_catalog=grounding.get_govoo_schema_catalog(),
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query},
        ]
        content, model_name, total_tokens = grounding.run_tool_loop(config, messages)
        return self._parse_matches(content), model_name, total_tokens

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
