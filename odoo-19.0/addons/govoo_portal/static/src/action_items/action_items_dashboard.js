/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

// Issue #266: replaces the role-based board.board Dashboard (issue #252)
// with one unified, personal action list. All FA4 icon names and plain
// Bootstrap colour-utility classes (never CSS custom properties, which
// don't exist in this backend bundle -- see kpi_strip.scss) are reused
// verbatim from the icon/colour choices already proven live by the old
// KPI strip (kpi_strip.js), not guessed: votes = info/fa-gavel (matches
// its old "resolutions" tile), meetings = primary/fa-calendar (matches
// its old "meetings" tile), contracts = secondary/fa-file-text-o (matches
// its old "expiringContracts" tile), filings = warning/fa-clock-o
// (matches its old "dueSoon" tile). Obligations is new (no old-tile
// precedent) and uses dark/fa-tasks -- fa-tasks is already used elsewhere
// in this codebase (govoo_contract_views.xml's Obligations stat button),
// so it's confirmed present in the shipped FA4 webfont too.
const TYPE_META = {
    vote: { color: "info", icon: "fa-gavel" },
    obligation: { color: "dark", icon: "fa-tasks" },
    contract: { color: "secondary", icon: "fa-file-text-o" },
    meeting: { color: "primary", icon: "fa-calendar" },
    filing: { color: "warning", icon: "fa-clock-o" },
};

const SECTION_META = [
    { key: "overdue", label: "Overdue", color: "danger" },
    { key: "week", label: "Due This Week", color: "warning" },
    { key: "upcoming", label: "Upcoming", color: "secondary" },
];

const EMPTY_DATA = {
    counts: { overdue: 0, week: 0, votes: 0, meetings: 0 },
    tabs: [{ key: "all", label: "All", count: 0 }],
    items: [],
    kpis: [],
};

export class GovooActionItemsDashboard extends Component {
    static template = "govoo_portal.ActionItemsDashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            activeTab: "all",
            data: EMPTY_DATA,
        });

        onWillStart(async () => {
            try {
                this.state.data = await this.orm.call(
                    "govoo.dashboard.action.items",
                    "get_my_action_items",
                    []
                );
            } catch {
                this.state.data = EMPTY_DATA;
            }
            this.state.loading = false;
        });
    }

    selectTab(key) {
        this.state.activeTab = key;
    }

    get visibleItems() {
        const items = this.state.data.items;
        const filtered =
            this.state.activeTab === "all"
                ? items
                : items.filter((item) => item.type === this.state.activeTab);
        return filtered.map((item) => ({ ...item, ...TYPE_META[item.type] }));
    }

    get sections() {
        const items = this.visibleItems;
        return SECTION_META.map((section) => ({
            ...section,
            items: items.filter((item) => item.group === section.key),
        }));
    }

    openRecord(item) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: item.res_model,
            res_id: item.res_id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openKpi(kpi) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: kpi.label,
            res_model: kpi.res_model,
            domain: kpi.domain,
            views: [
                [false, "list"],
                [false, "form"],
            ],
            target: "current",
        });
    }
}

registry.category("actions").add("govoo_action_items_dashboard", GovooActionItemsDashboard);
