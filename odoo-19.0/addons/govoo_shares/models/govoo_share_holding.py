# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooShareHolding(models.Model):
    """Computed/materialized cap table per (partner, share_class).

    Recomputed from allotments minus registered transfers.
    Does NOT inherit mail.thread — this is derived data, not user-edited.
    Audit trail is provided by mail.thread on allotment/transfer source records.
    """
    _name = 'govoo.share.holding'
    _description = 'Share Holding'
    _order = 'share_class_id, partner_id'

    _holding_partner_class_uniq = models.Constraint(
        'unique(partner_id, share_class_id)',
        'Only one holding record per partner per share class.',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shareholder',
        required=True,
        ondelete='restrict',
    )
    share_class_id = fields.Many2one(
        comodel_name='govoo.share.class',
        string='Share Class',
        required=True,
        ondelete='restrict',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='share_class_id.company_id',
        store=True,
        readonly=True,
    )
    quantity = fields.Integer(
        string='Shares Held',
        compute='_compute_holding',
        store=True,
    )
    percentage = fields.Float(
        string='Ownership %',
        compute='_compute_holding',
        store=True,
        digits=(5, 2),
    )
    voting_power = fields.Float(
        string='Voting Power',
        compute='_compute_holding',
        store=True,
    )

    @api.depends(
        'partner_id',
        'share_class_id',
        'share_class_id.allotment_ids.quantity',
        'share_class_id.allotment_ids.partner_id',
        'share_class_id.allotment_ids',
        'share_class_id.transfer_ids.quantity',
        'share_class_id.transfer_ids.transferor_id',
        'share_class_id.transfer_ids.transferee_id',
        'share_class_id.transfer_ids.state',
    )
    def _compute_holding(self):
        for rec in self:
            if not rec.share_class_id or not rec.partner_id:
                rec.quantity = 0
                rec.percentage = 0.0
                rec.voting_power = 0.0
                continue

            # Allotments for this partner+class
            allotments = self.env['govoo.share.allotment'].search([
                ('share_class_id', '=', rec.share_class_id.id),
                ('partner_id', '=', rec.partner_id.id),
            ])
            total_in = sum(allotments.mapped('quantity'))

            # Registered transfers OUT from this partner
            transfers_out = self.env['govoo.share.transfer'].search([
                ('share_class_id', '=', rec.share_class_id.id),
                ('transferor_id', '=', rec.partner_id.id),
                ('state', '=', 'registered'),
            ])
            total_out = sum(transfers_out.mapped('quantity'))

            # Registered transfers IN to this partner
            transfers_in = self.env['govoo.share.transfer'].search([
                ('share_class_id', '=', rec.share_class_id.id),
                ('transferee_id', '=', rec.partner_id.id),
                ('state', '=', 'registered'),
            ])
            total_transfer_in = sum(transfers_in.mapped('quantity'))

            qty = total_in - total_out + total_transfer_in
            if qty < 0:
                raise ValidationError(
                    _('Holding quantity would be negative for %s.') % rec.partner_id.name
                )

            rec.quantity = qty

            total_allotted = rec.share_class_id.total_allotted
            rec.percentage = (qty / total_allotted * 100) if total_allotted > 0 else 0.0
            rec.voting_power = qty * rec.share_class_id.votes_per_share

    @api.model
    def _recompute_holdings(self, share_class_id=False):
        """Recompute all holdings for a given share class (or all classes).

        Creates/deletes holding records as needed. The stored compute method
        (_compute_holding) fires automatically on create. For existing records
        whose dependencies changed, we invalidate to force recomputation.
        """
        domain = []
        if share_class_id:
            domain.append(('share_class_id', '=', share_class_id))

        # Get all (partner, class) pairs from allotments and transfers
        pairs = set()
        allotments = self.env['govoo.share.allotment'].search(domain)
        for a in allotments:
            pairs.add((a.partner_id.id, a.share_class_id.id))

        transfers = self.env['govoo.share.transfer'].search(domain + [('state', '!=', 'draft')])
        for t in transfers:
            pairs.add((t.transferor_id.id, t.share_class_id.id))
            pairs.add((t.transferee_id.id, t.share_class_id.id))

        # Create/update holding records
        existing = self.search(domain)
        existing_map = {(h.partner_id.id, h.share_class_id.id): h for h in existing}

        touched = self.browse()
        for partner_id, class_id in pairs:
            key = (partner_id, class_id)
            if key in existing_map:
                touched |= existing_map[key]
            else:
                new = self.create({
                    'partner_id': partner_id,
                    'share_class_id': class_id,
                })
                touched |= new

        # Delete holdings for pairs that no longer exist
        for h in existing:
            if h.id not in touched.ids:
                h.unlink()

        # Force recomputation by deleting and recreating holding records.
        # Stored computed fields can't be written to directly, so we must
        # trigger the compute via create(). This handles the case where
        # underlying allotment/transfer data changed but holding dependencies
        # (partner_id, share_class_id) didn't.
        existing = self.search(domain)
        existing_data = [(h.partner_id.id, h.share_class_id.id) for h in existing]
        existing.unlink()

        # Recreate holdings for all pairs
        final_holdings = self.browse()
        for partner_id, class_id in pairs:
            final_holdings |= self.create({
                'partner_id': partner_id,
                'share_class_id': class_id,
            })
        final_holdings._update_member_register()

        # Validate percentage sums to 100% per share class
        if share_class_id:
            classes = self.env['govoo.share.class'].browse(share_class_id)
        else:
            classes = touched.mapped('share_class_id')
        for sc in classes:
            holdings = self.search([('share_class_id', '=', sc.id)])
            total_pct = sum(holdings.mapped('percentage'))
            if holdings and abs(total_pct - 100.0) > 0.1:
                raise ValidationError(
                    _('Holdings for class "%s" sum to %.2f%%, expected 100%%.')
                    % (sc.name, total_pct)
                )

    def _update_member_register(self):
        """Update govoo.register.member records based on holdings."""
        Member = self.env['govoo.register.member']
        for rec in self:
            member = Member.search([
                ('partner_id', '=', rec.partner_id.id),
                ('company_id', '=', rec.company_id.id),
            ], limit=1)
            if rec.quantity > 0 and not member:
                Member.create({
                    'partner_id': rec.partner_id.id,
                    'company_id': rec.company_id.id,
                    'date_entered': fields.Date.context_today(rec),
                })
            elif rec.quantity <= 0 and member and not member.date_ceased:
                member.date_ceased = fields.Date.context_today(rec)
