# Part of Govoo. See LICENSE file for full copyright and licensing details.

import os
from unittest import mock

from cryptography.fernet import Fernet

from odoo.tests import TransactionCase

from ..models.govoo_ai_config import ENCRYPTION_KEY_ENV_VAR


class GovooAiTestBase(TransactionCase):
    """Shared setup for govoo_ai module tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.ai_user_group = cls.env.ref('govoo_ai.group_govoo_ai_user')
        cls.ai_admin_group = cls.env.ref('govoo_ai.group_govoo_ai_administrator')
        cls.ai_user = cls.env['res.users'].create({
            'name': 'AI User',
            'login': 'govoo_ai_user@example.com',
            'email': 'govoo_ai_user@example.com',
            'group_ids': [(6, 0, [cls.ai_user_group.id])],
        })
        # A deployment-level secret in real life; tests supply their own so
        # api_key can round-trip through encryption without touching the
        # real environment.
        patcher = mock.patch.dict(os.environ, {ENCRYPTION_KEY_ENV_VAR: Fernet.generate_key().decode()})
        patcher.start()
        cls.addClassCleanup(patcher.stop)

    def _make_active_config(self, cap=1000, api_key='test-key-123', enabled_features=('ai_f08',)):
        vals = {
            'company_id': self.company.id,
            'active': True,
            'monthly_token_cap': cap,
            'api_key': api_key,
        }
        vals.update({code: True for code in enabled_features})
        return self.env['govoo.ai.config'].create(vals)
