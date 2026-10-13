# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class GovooBoardCron(models.AbstractModel):
    """Issue #269 item 3: auto-close resolutions past their vote_deadline.
    A resolution only ever gets a vote_deadline when
    'govoo_board.resolution_voting_window_days' is configured (see
    govoo.resolution._voting_window_days) -- unconfigured, this cron finds
    nothing to do, matching the "no hard-coded legal values" convention
    already used by govoo_secretarial's and govoo_shares' reminder crons.
    """

    _name = 'govoo.board.cron'
    _description = 'Board/Resolution Scheduled Actions'

    @api.model
    def _cron_close_expired_resolutions(self):
        expired = self.env['govoo.resolution'].search([
            ('state', '=', 'open'),
            ('vote_deadline', '!=', False),
            ('vote_deadline', '<=', fields.Datetime.now()),
        ])
        for resolution in expired:
            try:
                resolution.action_tally()
            except Exception:
                # One resolution's tally failure (e.g. no eligible votes
                # cast at all, or a special resolution with an
                # unconfigured majority threshold) must not block every
                # other expired resolution in the same cron run.
                _logger.exception(
                    'Board: auto-close failed for resolution #%d (%s).',
                    resolution.id, resolution.title,
                )
