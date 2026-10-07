/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { _t } from "@web/core/l10n/translation";

// Issue #252: the Dashboard's own acceptance criteria ask for "KPI tiles"
// (upcoming meetings, open resolutions, overdue filings, expiring
// contracts) at a glance. board.board's own ArchParser (board_view.js)
// only recognises <board>/<column>/<action> nodes in its arch -- a
// <widget> tag there is silently dropped, never rendered -- so this
// component is mounted via a BoardController template/component patch
// (kpi_strip_board_patch.js), not as a view widget. It fetches its own
// counts via plain searchCount calls -- company scoping and visibility
// are entirely inherited from each model's own existing record rules, the
// same as the list/kanban widgets already on this page.
const EXPIRING_CONTRACT_WINDOW_DAYS = 60;

// Each tile's Bootstrap colour + FontAwesome 4 icon (this install ships the
// FA4 webfont, not FA5/6 -- confirmed against web/static/src/libs/
// fontawesome -- so icon names are chosen from that set only). Tiles are
// ordered most-urgent/actionable first, matching the dashboard's own
// urgency-ordering convention (issue #252).
const TILE_META = {
    overdue: { color: "danger", icon: "fa-exclamation-triangle" },
    resolutions: { color: "info", icon: "fa-gavel" },
    dueSoon: { color: "warning", icon: "fa-clock-o" },
    meetings: { color: "primary", icon: "fa-calendar" },
    boardPacks: { color: "dark", icon: "fa-folder-open-o" },
    expiringContracts: { color: "secondary", icon: "fa-file-text-o" },
};

export class GovooKpiStrip extends Component {
    static template = "govoo_portal.KpiStrip";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.tileMeta = TILE_META;
        this.state = useState({
            loading: true,
            meetingsCount: 0,
            resolutionsCount: 0,
            dueSoonCount: 0,
            overdueCount: 0,
            boardPacksCount: 0,
            expiringContractsCount: 0,
            // Hidden (not just zeroed) for Company Secretary / Board
            // Administrator, who cannot cast a vote (BR-SEC-004) -- same
            // restriction the "Open Resolutions Requiring My Vote" board
            // widget itself is gated on at the menu/action level.
            showResolutionsTile: true,
            // govoo.contract's own ir.model.access.csv only grants read to
            // Admin/Auditor/Contract Manager/Contract Approver -- NOT plain
            // group_govoo_user (most Board Directors), unlike every other
            // model this widget queries. Calling searchCount on it for an
            // ungated user raises an AccessError that, inside Promise.all,
            // fails ALL counts and breaks the whole dashboard -- confirmed
            // live as a Board Director. Must gate before querying, not
            // catch after.
            showContractsTile: true,
        });

        onWillStart(async () => {
            const [isSecretary, isAdmin, hasContractAccess] = await Promise.all([
                user.hasGroup("govoo_base.group_govoo_secretary"),
                user.hasGroup("govoo_base.group_govoo_admin"),
                Promise.all([
                    user.hasGroup("govoo_base.group_govoo_admin"),
                    user.hasGroup("govoo_base.group_govoo_auditor"),
                    user.hasGroup("govoo_base.group_govoo_contract_manager"),
                    user.hasGroup("govoo_base.group_govoo_contract_approver"),
                ]).then((flags) => flags.some(Boolean)),
            ]);
            this.state.showResolutionsTile = !isSecretary && !isAdmin;
            this.state.showContractsTile = hasContractAccess;
            await this.loadCounts();
        });
    }

    async loadCounts() {
        const counts = await Promise.all([
            this.orm.searchCount("govoo.meeting", [["state", "in", ["draft", "scheduled"]]]),
            this.state.showResolutionsTile
                ? this.orm.searchCount("govoo.resolution", [["requires_my_vote", "=", true]])
                : Promise.resolve(0),
            this.orm.searchCount("govoo.compliance.instance", [["rag_color", "=", "amber"]]),
            this.orm.searchCount("govoo.compliance.instance", [["rag_color", "=", "red"]]),
            this.orm.searchCount("govoo.board.pack", [["state", "!=", "distributed"]]),
            this.state.showContractsTile
                ? this.orm.searchCount("govoo.contract", [
                      ["state", "=", "active"],
                      ["date_end", "!=", false],
                      ["date_end", "<=", this.expiryWindowEnd()],
                  ])
                : Promise.resolve(0),
        ]);
        [
            this.state.meetingsCount,
            this.state.resolutionsCount,
            this.state.dueSoonCount,
            this.state.overdueCount,
            this.state.boardPacksCount,
            this.state.expiringContractsCount,
        ] = counts;
        this.state.loading = false;
    }

    expiryWindowEnd() {
        const d = new Date();
        d.setDate(d.getDate() + EXPIRING_CONTRACT_WINDOW_DAYS);
        return d.toISOString().slice(0, 10);
    }

    openMeetings() {
        this.action.doAction("govoo_portal.action_govoo_dashboard_meetings");
    }

    openResolutions() {
        this.action.doAction("govoo_portal.action_govoo_dashboard_my_votes");
    }

    openDueSoon() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Compliance Due Soon"),
            res_model: "govoo.compliance.instance",
            view_mode: "kanban,list",
            views: [
                [false, "kanban"],
                [false, "list"],
            ],
            domain: [["rag_color", "=", "amber"]],
        });
    }

    openOverdue() {
        this.action.doAction("govoo_portal.action_compliance_rag_dashboard");
    }

    openBoardPacks() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Pending Board Packs"),
            res_model: "govoo.board.pack",
            view_mode: "list,form",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: [["state", "!=", "distributed"]],
        });
    }

    openExpiringContracts() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Expiring Contracts"),
            res_model: "govoo.contract",
            view_mode: "list,form",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: [
                ["state", "=", "active"],
                ["date_end", "!=", false],
                ["date_end", "<=", this.expiryWindowEnd()],
            ],
        });
    }
}
