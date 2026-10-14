# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GovooMeetingRescheduleWizard(models.TransientModel):
    """Issue #271 item 2: prompts for the new date, then delegates to
    govoo.meeting.action_reschedule() -- all the actual cancel/copy logic
    lives on the meeting model itself, this is purely a date-input step."""

    _name = 'govoo.meeting.reschedule.wizard'
    _description = 'Reschedule Meeting Wizard'

    meeting_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Meeting',
        required=True,
    )
    new_date = fields.Datetime(
        string='New Date',
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        new_meeting = self.meeting_id.action_reschedule(self.new_date)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Meeting',
            'res_model': 'govoo.meeting',
            'view_mode': 'form',
            'res_id': new_meeting.id,
        }
