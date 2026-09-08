# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase


class GovooEvaluationTestBase(TransactionCase):
    """Shared setup for evaluation module tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Create a survey
        cls.survey = cls.env['survey.survey'].create({
            'title': 'Board Evaluation Survey',
            'survey_type': 'survey',
        })

        # Create a page (dimension) in the survey
        cls.page = cls.env['survey.question'].create({
            'survey_id': cls.survey.id,
            'title': 'Leadership',
            'is_page': True,
        })

        # Create a question on the page
        cls.question = cls.env['survey.question'].create({
            'survey_id': cls.survey.id,
            'page_id': cls.page.id,
            'title': 'How effective is the board chair?',
            'question_type': 'simple_choice',
        })

        # Create committee with members
        cls.committee = cls.env['govoo.committee'].create({
            'name': 'Audit Committee',
            'company_id': cls.company.id,
        })

        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Director A',
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Director B',
        })
        cls.partner_c = cls.env['res.partner'].create({
            'name': 'Director C',
        })

        # Create appointments for committee members
        cls.env['govoo.appointment'].create({
            'partner_id': cls.partner_a.id,
            'committee_id': cls.committee.id,
            'role': 'committee_member',
            'date_appointed': '2026-01-01',
            'company_id': cls.company.id,
        })
        cls.env['govoo.appointment'].create({
            'partner_id': cls.partner_b.id,
            'committee_id': cls.committee.id,
            'role': 'committee_member',
            'date_appointed': '2026-01-01',
            'company_id': cls.company.id,
        })

        # Create users for testing
        cls.user_secretary = cls.env['res.users'].create({
            'login': 'test_eval_secretary',
            'name': 'Test Secretary',
            'company_id': cls.company.id,
        })
        cls.user_secretary.write({
            'group_ids': [(4, cls.env.ref('govoo_base.group_govoo_secretary').id)],
        })
        cls.user_participant = cls.env['res.users'].create({
            'login': 'test_eval_participant',
            'name': 'Test Participant',
            'company_id': cls.company.id,
        })
        cls.user_participant.write({
            'group_ids': [
                (4, cls.env.ref('govoo_base.group_govoo_user').id),
                (4, cls.env.ref('survey.group_survey_user').id),
            ],
        })
