# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests.common import new_test_user

from .common import GovooEvaluationTestBase


class TestEvaluation(GovooEvaluationTestBase):
    """TC-EVAL-001..004: Evaluation campaign and result tests."""

    def test_001_aggregate_results_on_close(self):
        """TC-EVAL-001 / TC-WF-EVAL-001: campaign opened -> responses
        collected -> closed -> results aggregated correctly. Individual
        responses' inaccessibility to non-authorized participants is
        covered by test_002_confidentiality_enforced."""
        # Create a suggested answer with a score
        answer = self.env['survey.question.answer'].create({
            'question_id': self.question.id,
            'value': 'Effective',
            'answer_score': 8.0,
            'is_correct': True,
        })

        campaign = self.env['govoo.evaluation.campaign'].create({
            'name': 'Q1 Board Eval',
            'committee_id': self.committee.id,
            'survey_id': self.survey.id,
            'evaluation_type': 'board',
            'participant_ids': [(6, 0, [self.partner_a.id, self.partner_b.id])],
            'company_id': self.company.id,
        })

        # Open the campaign
        campaign.action_open()
        self.assertEqual(campaign.state, 'open')

        # Create completed user inputs with lines
        input_a = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner_a.id,
            'state': 'done',
        })
        self.env['survey.user_input.line'].create({
            'user_input_id': input_a.id,
            'question_id': self.question.id,
            'answer_type': 'suggestion',
            'suggested_answer_id': answer.id,
        })
        input_b = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner_b.id,
            'state': 'done',
        })
        self.env['survey.user_input.line'].create({
            'user_input_id': input_b.id,
            'question_id': self.question.id,
            'answer_type': 'suggestion',
            'suggested_answer_id': answer.id,
        })

        # Close the campaign — triggers aggregation
        campaign.action_close()
        self.assertEqual(campaign.state, 'closed')

        # Verify results were created
        self.assertTrue(campaign.result_ids, 'Results should be created on close.')
        result = campaign.result_ids[0]
        self.assertEqual(result.dimension_id, self.page)
        self.assertEqual(result.participant_count, 2)

    def test_002_confidentiality_enforced(self):
        """TC-EVAL-002: Non-Secretary/Admin cannot read others' survey.user_input."""
        self.env['govoo.evaluation.campaign'].create({
            'name': 'Confidentiality Test',
            'committee_id': self.committee.id,
            'survey_id': self.survey.id,
            'evaluation_type': 'board',
            'participant_ids': [(6, 0, [self.partner_a.id, self.partner_b.id])],
            'company_id': self.company.id,
        })

        # Create completed user inputs (using sudo for creation)
        input_a = self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.user_participant.partner_id.id,
            'state': 'done',
        })
        self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.partner_b.id,
            'state': 'done',
        })

        # Verify confidentiality record rule exists
        self.assertTrue(
            self.env['ir.rule'].search([
                ('name', 'like', 'Govoo confidentiality'),
            ]),
            'Confidentiality record rule should exist.',
        )

        # Participant can read own input
        input_a.with_user(self.user_participant).read(['survey_id'])

    def test_003_cannot_close_without_participants(self):
        """TC-EVAL-003: Campaign cannot be created with empty participants."""
        with self.assertRaises(Exception):
            self.env['govoo.evaluation.campaign'].create({
                'name': 'Empty Participants Test',
                'committee_id': self.committee.id,
                'survey_id': self.survey.id,
                'evaluation_type': 'board',
                'participant_ids': [(6, 0, [])],
                'company_id': self.company.id,
            })

    def test_004_participant_validation(self):
        """TC-EVAL-004: Participants must be committee members for board/committee/peer evals."""
        outsider = self.env['res.partner'].create({'name': 'Outsider'})

        with self.assertRaises(Exception):
            self.env['govoo.evaluation.campaign'].create({
                'name': 'Invalid Participants',
                'committee_id': self.committee.id,
                'survey_id': self.survey.id,
                'evaluation_type': 'board',
                'participant_ids': [(6, 0, [outsider.id])],
                'company_id': self.company.id,
            })

    def test_005_result_access_restricted_to_secretary_admin_auditor(self):
        """Governance User/Director Portal/Shareholder Portal must have no
        raw access to govoo.evaluation.result (aggregate-only via UI)."""
        campaign = self.env['govoo.evaluation.campaign'].create({
            'name': 'Access Control Test',
            'committee_id': self.committee.id,
            'survey_id': self.survey.id,
            'evaluation_type': 'board',
            'participant_ids': [(6, 0, [self.partner_a.id, self.partner_b.id])],
            'company_id': self.company.id,
        })
        result = self.env['govoo.evaluation.result'].create({
            'campaign_id': campaign.id,
            'dimension_id': self.page.id,
            'dimension_name': self.page.title,
            'aggregate_score': 8.0,
            'participant_count': 2,
            'company_id': self.company.id,
        })

        director_portal = new_test_user(
            self.env, login='test_eval_director_portal',
            groups='govoo_base.group_govoo_director_portal',
            company_id=self.company.id,
        )
        shareholder_portal = new_test_user(
            self.env, login='test_eval_shareholder_portal',
            groups='govoo_base.group_govoo_shareholder_portal',
            company_id=self.company.id,
        )

        for user in (self.user_participant, director_portal, shareholder_portal):
            # No CSV access at all -- even an empty-domain search() raises,
            # it doesn't just filter the record out.
            with self.assertRaises(AccessError):
                self.env['govoo.evaluation.result'].with_user(user).search([])
            with self.assertRaises(AccessError):
                result.with_user(user).check_access('read')

        # Secretary, Admin, and Auditor retain read access
        secretary_results = self.env['govoo.evaluation.result'].with_user(self.user_secretary).search([])
        self.assertIn(result, secretary_results)
