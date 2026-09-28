# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_STAGE_ORDER = ['pre_evaluation', 'technical_evaluation', 'financial_evaluation', 'awarded']


class GovooTender(models.Model):
    _name = 'govoo.tender'
    _description = 'Procurement Tender'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Tender Reference',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )
    tender_category_id = fields.Many2one(
        comodel_name='res.partner.category',
        string='Tender Category',
        tracking=True,
        help="Issue #205: reuses Odoo's native Contact Tags model "
             '(res.partner.category) so a tender\'s category and a '
             "vendor's own tags share the same vocabulary, rather than "
             'inventing a parallel category model. Tag a vendor with '
             "this same tag to record they're registered for this "
             'category of tender.',
    )
    bid_ids = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='govoo_tender_id',
        string='Vendor Bids',
        help='Each bid is a normal purchase.order (RFQ) -- vendor email '
             'invitation and the vendor bid-document portal already come '
             "from native Purchase (action_rfq_send, the portal.mixin-"
             'backed /my/purchase page and its attachment-capable '
             'chatter); nothing new is built for either.',
    )
    bid_count = fields.Integer(
        string='Bids',
        compute='_compute_bid_count',
    )
    evaluation_stage = fields.Selection(
        selection=[
            ('pre_evaluation', 'Pre-Evaluation'),
            ('technical_evaluation', 'Technical Evaluation'),
            ('financial_evaluation', 'Financial Evaluation'),
            ('awarded', 'Awarded'),
        ],
        string='Evaluation Stage',
        default='pre_evaluation',
        required=True,
        tracking=True,
    )
    evaluation_meeting_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Evaluation Committee Meeting',
        domain=[('meeting_type', '=', 'committee')],
        tracking=True,
        help='The committee meeting where bids were evaluated -- reuses '
             'govoo.meeting/govoo.minutes rather than a parallel model '
             '(issue #205 sub-task).',
    )
    evaluation_minutes_id = fields.Many2one(
        comodel_name='govoo.minutes',
        string='Evaluation Minutes',
        related='evaluation_meeting_id.minutes_id',
        readonly=True,
    )
    awarded_bid_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Awarded Bid',
        domain="[('id', 'in', bid_ids)]",
        tracking=True,
        copy=False,
    )

    @api.depends('bid_ids')
    def _compute_bid_count(self):
        for rec in self:
            rec.bid_count = len(rec.bid_ids)

    @api.constrains('awarded_bid_id', 'bid_ids')
    def _check_awarded_bid_is_a_bid(self):
        for rec in self:
            if rec.awarded_bid_id and rec.awarded_bid_id not in rec.bid_ids:
                raise ValidationError(
                    _("The awarded bid must be one of this tender's vendor bids.")
                )

    def _check_evaluation_stage_transition(self, target):
        for rec in self:
            current_index = _STAGE_ORDER.index(rec.evaluation_stage)
            target_index = _STAGE_ORDER.index(target)
            if target_index != current_index + 1:
                labels = dict(rec._fields['evaluation_stage'].selection)
                raise ValidationError(_(
                    'Evaluation stages must advance strictly forward. '
                    'Cannot move to "%(target)s" from "%(current)s".',
                    target=labels[target], current=labels[rec.evaluation_stage],
                ))

    def action_start_technical_evaluation(self):
        self._check_evaluation_stage_transition('technical_evaluation')
        self.write({'evaluation_stage': 'technical_evaluation'})

    def action_start_financial_evaluation(self):
        self._check_evaluation_stage_transition('financial_evaluation')
        self.write({'evaluation_stage': 'financial_evaluation'})

    def action_award(self):
        self._check_evaluation_stage_transition('awarded')
        for rec in self:
            if not rec.awarded_bid_id:
                raise ValidationError(
                    _('Select the awarded bid before marking this tender as Awarded.')
                )
        self.write({'evaluation_stage': 'awarded'})

    def action_view_bids(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bids'),
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('govoo_tender_id', '=', self.id)],
            'context': {'default_govoo_tender_id': self.id},
        }
