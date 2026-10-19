/** @odoo-module **/

import { registry } from "@web/core/registry";
import { PurchaseDashBoardListView, PurchaseDashBoardRenderer } from "@purchase/views/purchase_listview";
import { GovooProcurementKpiStrip } from "./kpi_strip";

// Adds a second, Clagov-styled card row to the Requests for Quotation
// list, alongside (not replacing) Odoo's own native dashboard cards
// above it -- this one surfaces a different, governance-relevant cut
// (tender-linked vs standalone RFQs, approval/confirmation status) that
// the native New/Sent/Late/Not Acknowledged/Late Receipt row doesn't
// already cover, rather than duplicating it.
const RFQ_TILES = [
    { label: "Tender-Linked RFQs", icon: "fa-gavel", color: "info", domain: () => [["govoo_tender_id", "!=", false], ["state", "in", ["draft", "sent"]]] },
    { label: "Standalone RFQs", icon: "fa-file-text-o", color: "secondary", domain: () => [["govoo_tender_id", "=", false], ["state", "in", ["draft", "sent"]]] },
    { label: "Pending Approval", icon: "fa-hourglass-half", color: "warning", domain: () => [["state", "=", "to approve"]] },
    { label: "Confirmed Orders", icon: "fa-check-circle", color: "success", domain: () => [["state", "=", "purchase"]] },
];

export class GovooPurchaseDashBoardRenderer extends PurchaseDashBoardRenderer {
    static template = "govoo_procurement.PurchaseDashBoardKpiRenderer";
    static components = {
        ...PurchaseDashBoardRenderer.components,
        GovooProcurementKpiStrip,
    };

    setup() {
        super.setup();
        this.kpiTiles = RFQ_TILES;
    }
}

registry.category("views").add("purchase_dashboard_list_govoo_kpi", {
    ...PurchaseDashBoardListView,
    Renderer: GovooPurchaseDashBoardRenderer,
});
