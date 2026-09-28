# Part of Govoo. See LICENSE file for full copyright and licensing details.

from unittest import mock

import requests

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import GovooAiTestBase


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiOpenAiClient(GovooAiTestBase):

    def test_raises_without_api_key(self):
        with self.assertRaises(UserError):
            self.env['govoo.ai.openai.client'].chat_completion(
                api_key=None, messages=[{'role': 'user', 'content': 'hi'}],
            )

    def test_raises_on_connection_error(self):
        client = self.env['govoo.ai.openai.client']
        with mock.patch('requests.post', side_effect=requests.ConnectionError('boom')):
            with self.assertRaises(UserError):
                client.chat_completion(
                    api_key='sk-test',
                    messages=[{'role': 'user', 'content': 'hi'}],
                )

    def test_raises_on_non_200_status(self):
        client = self.env['govoo.ai.openai.client']
        with mock.patch(
            'requests.post',
            return_value=_FakeResponse(status_code=401, text='invalid key'),
        ):
            with self.assertRaises(UserError):
                client.chat_completion(
                    api_key='sk-test',
                    messages=[{'role': 'user', 'content': 'hi'}],
                )

    def test_returns_parsed_json_on_success(self):
        client = self.env['govoo.ai.openai.client']
        fake_payload = {
            'model': 'gpt-4o-mini',
            'choices': [{'message': {'role': 'assistant', 'content': '{"matches": []}'}}],
            'usage': {'total_tokens': 42},
        }
        with mock.patch('requests.post', return_value=_FakeResponse(payload=fake_payload)):
            result = client.chat_completion(
                api_key='sk-test',
                messages=[{'role': 'user', 'content': 'hi'}],
            )
        self.assertEqual(result, fake_payload)

    def test_tools_included_in_payload_when_given(self):
        client = self.env['govoo.ai.openai.client']
        captured = {}

        def _fake_post(url, headers=None, json=None, timeout=None):
            captured.update(json)
            return _FakeResponse(payload={
                'model': 'gpt-4o-mini',
                'choices': [{'message': {'content': '{}'}}],
                'usage': {'total_tokens': 1},
            })

        tools = [{'type': 'function', 'function': {'name': 'search_read'}}]
        with mock.patch('requests.post', side_effect=_fake_post):
            client.chat_completion(
                api_key='sk-test',
                messages=[{'role': 'user', 'content': 'hi'}],
                tools=tools,
            )
        self.assertEqual(captured.get('tools'), tools)
