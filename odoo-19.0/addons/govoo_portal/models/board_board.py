# Part of Govoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import api, models

GOVOO_DASHBOARD_VIEW_XMLIDS = (
    'govoo_portal.govoo_board_dashboard_view',
    'govoo_portal.govoo_board_dashboard_view_no_vote',
)


class BoardBoard(models.AbstractModel):
    _inherit = 'board.board'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)
        if view_type == 'form' and view_id in self._govoo_dashboard_view_ids():
            # board.board only auto-creates a per-user ir.ui.view.custom row
            # through the stock "Add to Dashboard" flow (board/controllers/
            # main.py), which is hardcoded to board.open_board_my_dash_action
            # (Odoo's own "My Dashboard"). Any OTHER board.board view -- ours
            # included -- never gets one, so BoardController.saveBoard() sends
            # custom_id: undefined to /web/view/edit_custom the first time a
            # user changes layout, folds a column, or drags an action, and the
            # server 500s on the missing required argument. Scoped to our two
            # views only, not every board.board, so the stock "My Dashboard"
            # keeps its own normal (lazy, click-to-add) behaviour untouched.
            if 'custom_view_id' not in res:
                custom_view = self.env['ir.ui.view.custom'].sudo().create({
                    'user_id': self.env.uid,
                    'ref_id': view_id,
                    'arch': res['arch'],
                })
                res['custom_view_id'] = custom_view.id
            # Any user who already had a saved per-user layout (an
            # ir.ui.view.custom row) from BEFORE the KPI strip's
            # o_govoo_board_dashboard marker class was added to this view
            # has that marker baked out of their stored arch snapshot
            # forever -- the client-side patch that mounts the KPI strip
            # (kpi_strip_board_patch.js) keys off that exact class, so it
            # silently never renders for them again. Re-stamping the
            # marker onto whatever arch we're about to return (base or a
            # saved custom one) makes this self-healing without touching
            # the user's actual saved column/fold layout.
            res['arch'] = self._ensure_govoo_marker(res['arch'])
        return res

    def _govoo_dashboard_view_ids(self):
        ids = []
        for xmlid in GOVOO_DASHBOARD_VIEW_XMLIDS:
            view = self.env.ref(xmlid, raise_if_not_found=False)
            if view:
                ids.append(view.id)
        return ids

    def _ensure_govoo_marker(self, arch):
        root = etree.fromstring(arch)
        board_node = root.find('.//board')
        if board_node is not None:
            classes = set((board_node.get('class') or '').split())
            classes.add('o_govoo_board_dashboard')
            board_node.set('class', ' '.join(sorted(classes)))
        return etree.tostring(root, encoding='unicode')
