# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import AccessError

WEEK_WINDOW_DAYS = 7

# govoo.contract.obligation's own ir.model.access.csv grants read only to
# Admin/Auditor/Contract Manager/Contract Approver -- NOT plain
# group_govoo_user (most Board Directors), the exact same access boundary
# kpi_strip.js already had to gate govoo.contract behind for the same
# reason: calling search() for an ungated user raises an AccessError.
OBLIGATION_ACCESS_GROUPS = (
    'govoo_base.group_govoo_admin',
    'govoo_base.group_govoo_auditor',
    'govoo_base.group_govoo_contract_manager',
    'govoo_base.group_govoo_contract_approver',
)


class GovooDashboardActionItems(models.AbstractModel):
    """Issue #266: aggregates everything the CURRENT user personally needs
    to act on -- votes, contract obligations, contracts awaiting their
    approval, compliance filings, and meetings they're attending -- one
    query per model, as the calling user (never sudo()), so every model's
    own record rules and multi-company scoping apply for free. Replaces
    the role-based board.board Dashboard (issue #252), which only ever
    showed a team-wide overview, never a personal action list.

    Each per-type fetch is wrapped so a single model's AccessError (a
    permission gap we didn't anticipate, now or in the future) degrades
    that type to zero items instead of 500ing the whole dashboard.
    """

    _name = 'govoo.dashboard.action.items'
    _description = 'My Action Items aggregation for the unified Dashboard'

    @api.model
    def get_my_action_items(self):
        items = []
        for fetch in (
            self._get_vote_items,
            self._get_obligation_items,
            self._get_contract_items,
            self._get_filing_items,
            self._get_meeting_items,
        ):
            try:
                items += fetch()
            except AccessError:
                continue

        type_order = ['vote', 'obligation', 'contract', 'meeting', 'filing']
        type_labels = {
            'vote': 'Votes',
            'obligation': 'Obligations',
            'contract': 'Contracts',
            'meeting': 'Meetings',
            'filing': 'Filings',
        }
        tabs = [{'key': 'all', 'label': 'All', 'count': len(items)}]
        tabs += [
            {'key': t, 'label': type_labels[t], 'count': len([i for i in items if i['type'] == t])}
            for t in type_order
        ]

        counts = {
            'overdue': len([i for i in items if i['group'] == 'overdue']),
            'week': len([i for i in items if i['group'] == 'week']),
            'votes': len([i for i in items if i['type'] == 'vote']),
            'meetings': len([i for i in items if i['type'] == 'meeting']),
        }

        return {'counts': counts, 'tabs': tabs, 'items': items}

    def _has_any_group(self, xmlids):
        return any(self.env.user.has_group(xmlid) for xmlid in xmlids)

    def _bucket(self, due_date, overdue):
        if overdue:
            return 'overdue'
        if due_date is not None and (due_date - fields.Date.context_today(self)).days <= WEEK_WINDOW_DAYS:
            return 'week'
        return 'upcoming'

    def _format_due_label(self, days, overdue, prefix='Due'):
        if days is None:
            return 'No due date'
        if overdue:
            return 'Overdue %d day%s' % (-days, '' if -days == 1 else 's')
        if days == 0:
            return '%s today' % prefix
        return '%s in %d day%s' % (prefix, days, '' if days == 1 else 's')

    def _get_vote_items(self):
        resolutions = self.env['govoo.resolution'].search([('requires_my_vote', '=', True)])
        return [{
            'id': 'vote-%d' % r.id,
            'type': 'vote',
            'group': 'week',
            'title': r.title,
            'context': r.meeting_id.name or '',
            'due_label': 'Open for voting',
            'action_label': 'Cast Vote',
            'res_model': 'govoo.resolution',
            'res_id': r.id,
        } for r in resolutions]

    def _get_obligation_items(self):
        if not self._has_any_group(OBLIGATION_ACCESS_GROUPS):
            return []
        obligations = self.env['govoo.contract.obligation'].search([
            ('responsible_id', '=', self.env.uid),
            ('state', 'in', ('open', 'overdue')),
        ])
        today = fields.Date.context_today(self)
        results = []
        for o in obligations:
            overdue = o.state == 'overdue'
            days = (o.due_date - today).days if o.due_date else None
            results.append({
                'id': 'obligation-%d' % o.id,
                'type': 'obligation',
                'group': self._bucket(o.due_date, overdue),
                'title': o.name,
                'context': o.contract_id.name or '',
                'due_label': self._format_due_label(days, overdue),
                'action_label': 'Mark Done',
                'res_model': 'govoo.contract.obligation',
                'res_id': o.id,
            })
        return results

    def _get_contract_items(self):
        if not self.env.user.has_group('govoo_base.group_govoo_contract_approver'):
            return []
        contracts = self.env['govoo.contract'].search([('state', '=', 'in_approval')])
        return [{
            'id': 'contract-%d' % c.id,
            'type': 'contract',
            'group': 'week',
            'title': c.name,
            'context': c.counterparty_id.name or '',
            'due_label': 'Awaiting approval',
            'action_label': 'Review Contract',
            'res_model': 'govoo.contract',
            'res_id': c.id,
        } for c in contracts]

    def _get_filing_items(self):
        instances = self.env['govoo.compliance.instance'].search([
            ('responsible_id', '=', self.env.uid),
            ('state', 'in', ('upcoming', 'in_progress', 'late')),
        ])
        today = fields.Date.context_today(self)
        results = []
        for inst in instances:
            overdue = inst.state == 'late'
            days = (inst.due_date - today).days if inst.due_date else None
            results.append({
                'id': 'filing-%d' % inst.id,
                'type': 'filing',
                'group': self._bucket(inst.due_date, overdue),
                'title': inst.obligation_id.name or '',
                'context': inst.period or '',
                'due_label': self._format_due_label(days, overdue),
                'action_label': 'Record Filing',
                'res_model': 'govoo.compliance.instance',
                'res_id': inst.id,
            })
        return results

    def _get_meeting_items(self):
        partner = self.env.user.partner_id
        meetings = self.env['govoo.meeting'].search([
            ('attendee_ids', 'in', partner.id),
            ('state', 'in', ('draft', 'scheduled')),
        ])
        today = fields.Date.context_today(self)
        results = []
        for m in meetings:
            meeting_date = m.date.date() if m.date else None
            overdue = bool(meeting_date and meeting_date < today)
            days = (meeting_date - today).days if meeting_date else None
            results.append({
                'id': 'meeting-%d' % m.id,
                'type': 'meeting',
                'group': self._bucket(meeting_date, overdue),
                'title': m.name,
                'context': m.committee_id.name or '',
                'due_label': self._format_due_label(days, overdue, prefix='Meeting'),
                'action_label': 'View Agenda',
                'res_model': 'govoo.meeting',
                'res_id': m.id,
            })
        return results
