# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError

from .common import GovooEvaluationTestBase


class TestEvaluationResultWriteGuard(GovooEvaluationTestBase):
    """Issue #84: aggregate_score/participant_count cannot be
    hand-edited outside the aggregation code path."""

    def setUp(self):
        super().setUp()
        self.campaign = self.env['govoo.evaluation.campaign'].create({
            'name': 'Guard Test Campaign',
            'committee_id': self.committee.id,
            'survey_id': self.survey.id,
            'evaluation_type': 'board',
            'participant_ids': [(6, 0, [self.partner_a.id])],
            'company_id': self.company.id,
        })
        self.result = self.env['govoo.evaluation.result'].with_context(
            govoo_aggregation=True,
        ).create({
            'campaign_id': self.campaign.id,
            'dimension_id': self.page.id,
            'aggregate_score': 5.0,
            'participant_count': 1,
        })

    def test_direct_write_to_aggregate_score_rejected(self):
        # self.result's recordset still carries govoo_aggregation=True
        # from its creation in setUp -- with_user() only swaps the
        # user, not the context -- so explicitly clear it here to test
        # the actual direct-write (no context flag) path.
        with self.assertRaises(UserError):
            self.result.with_user(self.user_secretary).with_context(
                govoo_aggregation=False,
            ).write({'aggregate_score': 9.9})

    def test_direct_create_with_aggregate_score_rejected(self):
        with self.assertRaises(UserError):
            self.env['govoo.evaluation.result'].with_user(self.user_secretary).create({
                'campaign_id': self.campaign.id,
                'dimension_id': self.page.id,
                'aggregate_score': 9.9,
            })

    def test_aggregation_code_path_still_works(self):
        """_aggregate_results() (via action_close) legitimately sets
        these fields through the govoo_aggregation context flag."""
        answer = self.env['survey.question.answer'].create({
            'question_id': self.question.id,
            'value': 'Effective',
            'answer_score': 8.0,
            'is_correct': True,
        })
        self.campaign.action_open()
        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner_a.id,
            'state': 'done',
        })
        self.env['survey.user_input.line'].create({
            'user_input_id': user_input.id,
            'question_id': self.question.id,
            'answer_type': 'suggestion',
            'suggested_answer_id': answer.id,
        })
        self.campaign.action_close()
        result = self.env['govoo.evaluation.result'].search([
            ('campaign_id', '=', self.campaign.id),
            ('dimension_id', '=', self.page.id),
        ])
        self.assertTrue(result)
        self.assertEqual(result.aggregate_score, 8.0)
