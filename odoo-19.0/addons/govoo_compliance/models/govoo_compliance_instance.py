# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooComplianceInstance(models.Model):
    _name = 'govoo.compliance.instance'
    _description = 'Compliance Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date asc'

    _instance_obligation_company_period_uniq = models.Constraint(
        'unique(obligation_id, company_id, period)',
        'Only one instance per obligation per company per period.',
    )

    obligation_id = fields.Many2one(
        comodel_name='govoo.compliance.obligation',
        string='Obligation',
        required=True,
        ondelete='restrict',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )
    period = fields.Char(
        string='Period',
        help='e.g. "2027-Q1", "2027".',
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        tracking=True,
    )
    responsible_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('upcoming', 'Upcoming'),
            ('in_progress', 'In Progress'),
            ('filed', 'Filed'),
            ('late', 'Late'),
            ('waived', 'Waived'),
        ],
        string='Status',
        default='upcoming',
        required=True,
        tracking=True,
    )
    filed_date = fields.Date(
        string='Filed Date',
    )
    reference_no = fields.Char(
        string='Filing Reference',
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a document is generated for this field, check
    # self.env['govoo.feature.flags'].is_documents_app_installed() to
    # additionally file a copy into the Documents workspace.
    filing_document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Filing Document',
    )
    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Filing Attachment',
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )
    days_to_due = fields.Integer(
        string='Days to Due',
        compute='_compute_days_to_due',
        store=True,
    )
    rag_color = fields.Selection(
        selection=[
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red'),
            ('grey', 'Grey'),
        ],
        string='RAG Status',
        compute='_compute_rag_color',
        store=True,
    )

    @api.depends('obligation_id', 'period', 'company_id')
    def _compute_name(self):
        for rec in self:
            parts = [rec.obligation_id.name or '']
            if rec.period:
                parts.append(rec.period)
            if rec.company_id:
                parts.append(rec.company_id.name)
            rec.name = ' - '.join(parts) if parts else ''

    @api.depends('due_date', 'state')
    def _compute_days_to_due(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.due_date:
                rec.days_to_due = (rec.due_date - today).days
            else:
                rec.days_to_due = 0

    @api.depends('state', 'days_to_due', 'obligation_id.lead_time_days')
    def _compute_rag_color(self):
        for rec in self:
            if rec.state in ('filed', 'waived'):
                rec.rag_color = 'grey'
            elif rec.state == 'late':
                rec.rag_color = 'red'
            elif rec.state in ('upcoming', 'in_progress'):
                lead = rec.obligation_id.lead_time_days or 0
                if rec.days_to_due <= lead:
                    rec.rag_color = 'amber'
                else:
                    rec.rag_color = 'green'
            else:
                rec.rag_color = 'grey'

    @api.constrains('state')
    def _check_state_terminal(self):
        """filed/waived are terminal — no transitions out."""
        # Enforced via write overrides below

    def write(self, vals):
        """Block transitions from terminal states."""
        terminal = ('filed', 'waived')
        if 'state' in vals:
            for rec in self:
                if rec.state in terminal:
                    raise ValidationError(
                        _('Cannot change status from "%s" to "%s". '
                          'Filed and Waived are terminal states.')
                        % (rec.state, vals['state']),
                    )
        return super().write(vals)

    def action_start(self):
        """upcoming → in_progress: responsible user begins work."""
        for rec in self:
            if rec.state != 'upcoming':
                raise ValidationError(_('Only Upcoming instances can be started.'))
        self.write({'state': 'in_progress'})

    def action_file(self):
        """in_progress/late → filed: filing recorded (BR-COMP-004)."""
        for rec in self:
            if rec.state not in ('in_progress', 'late'):
                raise ValidationError(_('Only In Progress or Late instances can be filed.'))
            if not rec.reference_no or not rec.filed_date:
                raise ValidationError(
                    _('Filing Reference and Filed Date are required to record a filing.')
                )
        self.write({'state': 'filed'})

    def action_waive(self):
        """Any non-terminal → waived: Secretary/Admin marks not applicable."""
        for rec in self:
            if rec.state in ('filed', 'waived'):
                raise ValidationError(_('Cannot waive a Filed or Waived instance.'))
        self.write({'state': 'waived'})

    def action_generate_filing_pack(self):
        """Assemble filing-ready documents for manual portal upload.

        No assumption of automated RDB/Irembo API (BR-COMP-004).
        Feature-flagged: stores as documents.document on Enterprise,
        ir.attachment fallback on Community.
        """
        self.ensure_one()
        # Generate filing pack report
        report = self.env.ref('govoo_compliance.action_report_filing_pack')
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report.id, self.ids,
        )
        attachment = self.env['ir.attachment'].create({
            'name': 'Filing Pack - %s - %s.pdf' % (
                self.obligation_id.name, self.period or 'N/A',
            ),
            'type': 'binary',
            'datas': pdf_content,
            'res_model': self._name,
            'res_id': self.id,
        })
        self.attachment_id = attachment
        if self.env['govoo.feature.flags'].is_documents_app_installed():
            # ir.attachment (self.attachment_id) remains the source of
            # truth either way; this additionally files a copy into the
            # Documents workspace for clients with that app.
            self.env['documents.document'].sudo().create({
                'name': attachment.name,
                'attachment_id': attachment.id,
            })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'target': 'new',
        }
