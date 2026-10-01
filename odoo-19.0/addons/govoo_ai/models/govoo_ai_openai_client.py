# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

OPENAI_CHAT_COMPLETIONS_URL = 'https://api.openai.com/v1/chat/completions'

# [CONFIRM] No specific OpenAI model is named anywhere in the addendum or in
# decisions/confirmed-decisions.md entry [24] (which confirms the provider,
# not the model). gpt-4o-mini is used as a reasonable, cost-conscious
# default for a metered add-on -- not asserted as a confirmed decision.
# Kept as a parameter, never hard-coded into a call site.
DEFAULT_MODEL = 'gpt-4o-mini'

REQUEST_TIMEOUT_SECONDS = 30


class GovooAiOpenAiClient(models.AbstractModel):
    """Thin OpenAI Chat Completions client.

    Deliberately a plain ``requests`` call, not the ``openai`` Python SDK:
    one fewer dependency to keep patched on every client's self-hosted
    server, for a single, stable, well-documented REST endpoint. Callers
    never see the raw HTTP response -- only its ``choices[0].message`` and
    ``usage`` are ever consumed elsewhere in govoo_ai.
    """

    _name = 'govoo.ai.openai.client'
    _description = 'OpenAI Chat Completions Client'

    def chat_completion(self, api_key, messages, tools=None, model=None):
        """Call the Chat Completions API and return the parsed JSON response.

        :raise UserError: if ``api_key`` is empty, the request fails to
            reach the provider, or the provider returns a non-200 status.
        """
        if not api_key:
            raise UserError(_('No AI provider API key is configured for this company.'))
        payload = {
            'model': model or DEFAULT_MODEL,
            'messages': messages,
            # Tool-calling orchestration needs consistent, well-formed
            # arguments (a domain is strict JSON syntax, not prose) over
            # creative variance, so 0 is the principled choice here. Note:
            # live testing found this does NOT eliminate every malformed
            # Odoo domain (gpt-4o-mini occasionally still drops the outer
            # wrapping list on a single free-text condition, even though
            # both this prompt and muk_mcp's own tool description show the
            # correct form) -- that remains a known, documented model
            # limitation, not something this setting fixes outright.
            'temperature': 0,
        }
        if tools:
            payload['tools'] = tools
        try:
            response = requests.post(
                OPENAI_CHAT_COMPLETIONS_URL,
                headers={
                    'Authorization': 'Bearer %s' % api_key,
                    'Content-Type': 'application/json',
                },
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            _logger.warning('OpenAI request failed: %s', exc)
            raise UserError(_('Could not reach the AI provider: %s') % exc)
        if response.status_code != 200:
            _logger.warning(
                'OpenAI returned status %s: %s',
                response.status_code, response.text[:500],
            )
            raise UserError(_(
                'The AI provider returned an error (status %s). Contact '
                'your AI Administrator if this persists.'
            ) % response.status_code)
        return response.json()
