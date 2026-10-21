# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GovooMeeting(models.Model):
    _inherit = 'govoo.meeting'

    # Issue #329: the Legal Officer's record rule on govoo.minutes needs a
    # dotted-path domain reaching govoo.tender.evaluation_stage, but
    # govoo.meeting has no reverse link back to govoo.tender (confirmed
    # during #337's own investigation too). ir.rule domain_force is
    # evaluated with only user/company_ids/company_id in scope (no env),
    # so a dynamic subquery isn't an option -- this has to be a real
    # field. Maintained by govoo.tender's create()/write()
    # (_sync_evaluation_meeting_tender_links), not computed: there's no
    # actual reverse relation to @api.depends on since Many2one fields
    # don't auto-generate a reverse One2many.
    evaluation_tender_id = fields.Many2one(
        comodel_name='govoo.tender',
        string='Evaluation For Tender',
        readonly=True,
        copy=False,
    )
    # Issue #357: which of the tender's two evaluation phases this
    # meeting actually is -- evaluation_tender_id alone doesn't say,
    # and the Procurement Officer's own narrowed agenda/minutes access
    # needs that distinction (Financial Evaluation only, never
    # Technical). Same reasoning and maintenance discipline as
    # evaluation_tender_id above: a real, stored field kept in sync by
    # _sync_evaluation_meeting_tender_links, since ir.rule domain_force
    # has no env access for a dynamic lookup.
    evaluation_phase = fields.Selection(
        selection=[
            ('technical', 'Technical Evaluation'),
            ('financial', 'Financial Evaluation'),
        ],
        string='Evaluation Phase',
        readonly=True,
        copy=False,
    )
