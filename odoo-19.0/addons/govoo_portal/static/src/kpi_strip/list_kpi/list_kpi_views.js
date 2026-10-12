/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { makeGovooKpiListController } from "./list_kpi_controller";

const CONTRACT_EXPIRY_WINDOW_DAYS = 60;

function contractExpiryWindowEnd() {
    const d = new Date();
    d.setDate(d.getDate() + CONTRACT_EXPIRY_WINDOW_DAYS);
    return d.toISOString().slice(0, 10);
}

// Issue #261. Filters/colours/icons match the plan approved on the issue
// before implementation. All FA4 icon names (this install ships the FA4
// webfont, not FA5/6) and plain Bootstrap colour-utility classes (not CSS
// custom properties -- those don't exist in the backend bundle, the cause
// of #260's "KPI cards have no colour" bug).
const MEETING_TILES = [
    { label: "Upcoming", icon: "fa-calendar", color: "primary", domain: () => [["state", "=", "scheduled"]] },
    { label: "Draft", icon: "fa-pencil", color: "warning", domain: () => [["state", "=", "draft"]] },
    { label: "Awaiting Minutes", icon: "fa-file-text-o", color: "danger", domain: () => [["state", "=", "held"]] },
    {
        label: "Quorum Not Met",
        icon: "fa-exclamation-triangle",
        color: "danger",
        domain: () => [["quorum_met", "=", false], ["state", "!=", "draft"]],
    },
];

const RESOLUTION_TILES = [
    { label: "Open for Voting", icon: "fa-gavel", color: "info", domain: () => [["state", "=", "open"]] },
    { label: "Passed", icon: "fa-check-circle", color: "success", domain: () => [["state", "=", "passed"]] },
    { label: "Failed", icon: "fa-times-circle", color: "danger", domain: () => [["state", "=", "failed"]] },
    { label: "Draft", icon: "fa-pencil", color: "secondary", domain: () => [["state", "=", "draft"]] },
];

const CONTRACT_TILES = [
    { label: "Active", icon: "fa-file-text-o", color: "primary", domain: () => [["state", "=", "active"]] },
    {
        label: "Expiring in 60 Days",
        icon: "fa-clock-o",
        color: "warning",
        domain: () => [
            ["state", "=", "active"],
            ["date_end", "!=", false],
            ["date_end", "<=", contractExpiryWindowEnd()],
        ],
    },
    { label: "Pending Signature", icon: "fa-pencil-square-o", color: "info", domain: () => [["sign_status", "=", "sent"]] },
    { label: "In Approval", icon: "fa-hourglass-half", color: "dark", domain: () => [["state", "=", "in_approval"]] },
];

const OBLIGATION_TILES = [
    { label: "Overdue", icon: "fa-exclamation-triangle", color: "danger", domain: () => [["state", "=", "overdue"]] },
    {
        label: "Due Soon",
        icon: "fa-clock-o",
        color: "warning",
        domain: () => [["rag_color", "=", "amber"], ["state", "=", "open"]],
    },
    { label: "Open", icon: "fa-list", color: "primary", domain: () => [["state", "=", "open"]] },
    { label: "Waived", icon: "fa-ban", color: "secondary", domain: () => [["state", "=", "waived"]] },
];

const COMPLIANCE_INSTANCE_TILES = [
    { label: "Late", icon: "fa-exclamation-triangle", color: "danger", domain: () => [["state", "=", "late"]] },
    { label: "Due Soon", icon: "fa-clock-o", color: "warning", domain: () => [["rag_color", "=", "amber"]] },
    { label: "Filed", icon: "fa-check-circle", color: "success", domain: () => [["state", "=", "filed"]] },
    { label: "Upcoming", icon: "fa-calendar", color: "primary", domain: () => [["state", "=", "upcoming"]] },
];

function registerGovooKpiListView(name, tiles) {
    registry.category("views").add(name, {
        ...listView,
        Controller: makeGovooKpiListController(tiles),
    });
}

registerGovooKpiListView("govoo_meeting_kpi_list", MEETING_TILES);
registerGovooKpiListView("govoo_resolution_kpi_list", RESOLUTION_TILES);
registerGovooKpiListView("govoo_contract_kpi_list", CONTRACT_TILES);
registerGovooKpiListView("govoo_contract_obligation_kpi_list", OBLIGATION_TILES);
registerGovooKpiListView("govoo_compliance_instance_kpi_list", COMPLIANCE_INSTANCE_TILES);
