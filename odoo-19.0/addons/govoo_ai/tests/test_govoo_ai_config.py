# Part of Govoo. See LICENSE file for full copyright and licensing details.

import os
from unittest import mock

from cryptography.fernet import Fernet

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from ..models.govoo_ai_config import ENCRYPTION_KEY_ENV_VAR
from .common import GovooAiTestBase


@tagged('post_install', '-at_install', 'govoo_ai')
class TestGovooAiConfig(GovooAiTestBase):

    def test_config_inactive_by_default(self):
        config = self.env['govoo.ai.config'].create({'company_id': self.company.id})
        self.assertFalse(config.active)
        self.assertEqual(config.monthly_token_cap, 0)
        self.assertFalse(config.api_key)
        self.assertFalse(config.ai_f08)

    def test_activating_without_cap_raises(self):
        with self.assertRaises(ValidationError):
            self.env['govoo.ai.config'].create({
                'company_id': self.company.id,
                'active': True,
                'monthly_token_cap': 0,
                'api_key': 'test-key',
            })

    def test_activating_without_api_key_raises(self):
        with self.assertRaises(ValidationError):
            self.env['govoo.ai.config'].create({
                'company_id': self.company.id,
                'active': True,
                'monthly_token_cap': 500,
            })

    def test_activating_with_cap_and_key_succeeds(self):
        config = self._make_active_config(cap=500)
        self.assertTrue(config.active)

    def test_only_one_config_per_company(self):
        self._make_active_config()
        with self.assertRaises(Exception):
            self.env['govoo.ai.config'].create({
                'company_id': self.company.id,
                'active': True,
                'monthly_token_cap': 100,
                'api_key': 'another-key',
            })

    def test_is_feature_enabled(self):
        config = self._make_active_config(enabled_features=('ai_f08',))
        self.assertTrue(config.is_feature_enabled('ai_f08'))
        self.assertFalse(config.is_feature_enabled('ai_f09'))
        self.assertFalse(config.is_feature_enabled('ai_f01'))

    def test_is_feature_enabled_false_when_inactive(self):
        config = self.env['govoo.ai.config'].create({
            'company_id': self.company.id,
            'ai_f08': True,
        })
        self.assertFalse(config.is_feature_enabled('ai_f08'))

    def test_is_feature_enabled_unknown_code_raises(self):
        config = self._make_active_config()
        with self.assertRaises(ValueError):
            config.is_feature_enabled('not_a_real_feature')

    def test_api_key_round_trips_through_encryption(self):
        config = self._make_active_config(api_key='sk-super-secret-value')
        self.assertEqual(config.api_key, 'sk-super-secret-value')
        self.assertNotEqual(config.api_key_encrypted, 'sk-super-secret-value')
        self.assertTrue(config.api_key_encrypted)

    def test_setting_api_key_without_encryption_key_env_raises(self):
        with mock.patch.dict(os.environ):
            os.environ.pop(ENCRYPTION_KEY_ENV_VAR, None)
            with self.assertRaises(ValidationError):
                self.env['govoo.ai.config'].create({
                    'company_id': self.company.id,
                    'api_key': 'sk-should-not-save',
                })

    def test_decrypt_fails_gracefully_when_encryption_key_rotated(self):
        config = self._make_active_config(api_key='sk-original-value')
        with mock.patch.dict(os.environ, {ENCRYPTION_KEY_ENV_VAR: Fernet.generate_key().decode()}):
            config.invalidate_recordset(['api_key'])
            self.assertFalse(config.api_key)
