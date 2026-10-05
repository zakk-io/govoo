# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models


class GovooAiSearchWizard(models.TransientModel):
    """Search Governance Records (AI-F08) -- the single-question wizard
    shell agreed on for #216: one query in, a list of matched records with
    citations out, then "Search Again" or "Close". Deliberately not a
    multi-turn chat (that complexity, and the narrative-answer synthesis
    that comes with it, is AI-F09 / issue #217, which reuses this same
    grounding bridge)."""

    _name = 'govoo.ai.search.wizard'
    _description = 'Search Governance Records (AI-F08)'

    query = fields.Text(
        string='Your Question',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done'),
        ],
        default='draft',
    )
    request_id = fields.Many2one(
        comodel_name='govoo.ai.request',
        readonly=True,
    )
    result_ids = fields.Many2many(
        comodel_name='govoo.ai.suggestion',
        readonly=True,
    )
    result_count = fields.Integer(
        compute='_compute_result_count',
    )

    def _compute_result_count(self):
        for rec in self:
            rec.result_count = len(rec.result_ids)

    def action_search(self):
        self.ensure_one()
        suggestions = self.env['govoo.ai.search'].run(self.query)
        self.write({
            'state': 'done',
            'request_id': suggestions.request_id.id if suggestions else False,
            'result_ids': [(6, 0, suggestions.ids)],
        })
        return self._reopen()

    def action_search_suggested(self):
        """Run one of the ready-made example queries shown as chips on the
        draft screen -- each one individually re-verified live against a
        real OpenAI key and this deployment's actual data (not just
        reused from issue #216's original testing, since an LLM-backed
        search is not perfectly deterministic run to run -- two of the
        original eight example queries timed out/found nothing on
        re-check and were swapped out for ones that held up), so someone
        new to this feature has a one-click way to see it actually work
        before typing their own question. The button passes which
        example via its own `suggested_query` context key."""
        self.ensure_one()
        query = self.env.context.get('suggested_query')
        if query:
            self.query = query
        return self.action_search()

    def action_reset(self):
        self.ensure_one()
        self.write({
            'query': False,
            'state': 'draft',
            'request_id': False,
            'result_ids': [(5, 0, 0)],
        })
        return self._reopen()

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Search Governance Records'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
