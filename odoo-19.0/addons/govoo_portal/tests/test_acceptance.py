# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install', 'govoo_portal')
class TestAcceptanceCrossCutting(HttpCase):
    """TC-ACC-005, TC-ACC-007: cross-cutting acceptance scenarios that
    need every governance module (only govoo_portal depends on all of
    them)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env['res.company'].create({'name': 'Other Co'})

        cls.user_a = new_test_user(
            cls.env, login='test_acc_user_a',
            groups='govoo_base.group_govoo_user',
            company_id=cls.company_a.id,
        )

        cls.committee_a = cls.env['govoo.committee'].create({
            'name': 'Committee A',
            'company_id': cls.company_a.id,
        })
        cls.committee_b = cls.env['govoo.committee'].create({
            'name': 'Committee B',
            'company_id': cls.company_b.id,
        })

        cls.meeting_b = cls.env['govoo.meeting'].create({
            'name': 'Other Co Meeting',
            'committee_id': cls.committee_b.id,
            'meeting_type': 'board',
            'date': '2026-04-01 10:00:00',
            'company_id': cls.company_b.id,
        })

        cls.share_class_b = cls.env['govoo.share.class'].create({
            'name': 'Other Co Shares',
            'total_authorised': 1000,
            'company_id': cls.company_b.id,
        })
        holder_b = cls.env['res.partner'].create({
            'name': 'Other Co Holder',
            'company_id': cls.company_b.id,
        })
        cls.env['govoo.share.allotment'].create({
            'share_class_id': cls.share_class_b.id,
            'partner_id': holder_b.id,
            'quantity': 100,
            'date_allotted': '2026-01-01',
        })
        cls.holding_b = cls.env['govoo.share.holding'].search([
            ('share_class_id', '=', cls.share_class_b.id),
            ('partner_id', '=', holder_b.id),
        ], limit=1)

        obligation_b = cls.env['govoo.compliance.obligation'].create({
            'name': 'Other Co Obligation',
            'authority': 'RDB',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 31,
            'fixed_month': 3,
            'active': True,
            'company_id': cls.company_b.id,
        })
        cls.env['govoo.compliance.cron']._cron_generate_instances()
        cls.instance_b = cls.env['govoo.compliance.instance'].search([
            ('obligation_id', '=', obligation_b.id),
        ], limit=1)

        survey_b = cls.env['survey.survey'].create({
            'title': 'Other Co Survey',
            'survey_type': 'survey',
        })
        cls.env['survey.question'].create({
            'survey_id': survey_b.id,
            'title': 'Dimension',
            'is_page': True,
        })
        participant_b = cls.env['res.partner'].create({
            'name': 'Other Co Participant',
            'company_id': cls.company_b.id,
        })
        cls.env['govoo.appointment'].create({
            'partner_id': participant_b.id,
            'committee_id': cls.committee_b.id,
            'role': 'committee_member',
            'company_id': cls.company_b.id,
            'date_appointed': '2026-01-01',
        })
        cls.campaign_b = cls.env['govoo.evaluation.campaign'].create({
            'name': 'Other Co Eval',
            'committee_id': cls.committee_b.id,
            'survey_id': survey_b.id,
            'evaluation_type': 'board',
            'participant_ids': [(6, 0, [participant_b.id])],
            'company_id': cls.company_b.id,
        })

        cls.director_a = new_test_user(
            cls.env, login='test_acc_director_a',
            groups='govoo_base.group_govoo_director_portal',
            company_id=cls.company_a.id,
        )

    def _password(self, login):
        return login + 'x' * (8 - len(login))

    def test_multicompany_isolation_across_governance_models(self):
        """TC-ACC-005: multi-company isolation holds across every
        governance model — access denied cross-company."""
        for model_name, record in (
            ('govoo.meeting', self.meeting_b),
            ('govoo.share.holding', self.holding_b),
            ('govoo.compliance.instance', self.instance_b),
            ('govoo.evaluation.campaign', self.campaign_b),
        ):
            self.assertTrue(record, '%s fixture record should exist' % model_name)
            found = self.env[model_name].with_user(self.user_a).search([
                ('id', '=', record.id),
            ])
            self.assertFalse(
                found,
                '%s in another company should not be visible to a user_a scoped '
                'to company_a.' % model_name,
            )
            with self.assertRaises(Exception):
                record.with_user(self.user_a).check_access('read')

    def test_portal_direct_url_denied_outside_scope(self):
        """TC-ACC-007: portal record-rule enforcement, not menu-hiding —
        direct-URL access outside scope is denied even via a valid
        access_token (BR-SEC-006)."""
        token = self.meeting_b._portal_ensure_token()
        self.authenticate('test_acc_director_a', self._password('test_acc_director_a'))

        response = self.url_open('/my/meetings/%s' % self.meeting_b.id)
        self.assertNotIn(self.meeting_b.name, response.text)

        response = self.url_open(
            '/my/meetings/%s?access_token=%s' % (self.meeting_b.id, token),
        )
        self.assertNotIn(self.meeting_b.name, response.text)
