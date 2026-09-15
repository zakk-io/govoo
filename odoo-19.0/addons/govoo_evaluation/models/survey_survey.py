# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    govoo_evaluation_campaign_ids = fields.One2many(
        comodel_name='govoo.evaluation.campaign',
        inverse_name='survey_id',
        string='Govoo Evaluation Campaigns',
        help='Used to identify surveys used by a Govoo evaluation campaign, '
             'so the confidentiality override in '
             'govoo_evaluation_security.xml (BR-EVAL-001, issue #110) can '
             'scope itself to those surveys only, without affecting '
             'unrelated Survey app usage.',
    )
