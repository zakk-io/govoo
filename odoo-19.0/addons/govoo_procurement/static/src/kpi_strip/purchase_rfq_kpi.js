/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FileUploadListRenderer } from "@account/views/file_upload_list/file_upload_list_renderer";
import { fileUploadListView } from "@account/views/file_upload_list/file_upload_list_view";
import { PurchaseFileUploadListController } from "@purchase/views/purchase_listview";
import { GovooProcurementKpiStrip } from "./kpi_strip";

// Live feedback: having both Odoo's native dashboard row AND a second,
// Clagov-styled row stacked on top of each other was redundant and
// cluttered. This replaces the native row outright with a single
// consolidated strip that keeps its most useful metrics (New, Late RFQ,
// Not Acknowledged, Pending Approval -- reusing those same named filters
// from view_purchase_order_filter) plus the one governance-relevant cut
// the native row didn't have (Tender-Linked RFQs, a new filter added in
// govoo_procurement_kpi_views.xml). File upload (PurchaseFileUploader)
// lives in the Controller template (purchase.ListView), not the
// Renderer, so it's untouched by swapping the Renderer base here.
function lateCutoff() {
    return new Date().toISOString().slice(0, 19).replace("T", " ");
}

const RFQ_TILES = [
    { label: "New", icon: "fa-file-text-o", color: "info", domain: () => [["state", "=", "draft"]], filterNames: ["draft_rfqs"] },
    { label: "Late RFQ", icon: "fa-exclamation-triangle", color: "danger", domain: () => [["state", "in", ["draft", "sent", "to approve"]], ["date_order", "<", lateCutoff()]], filterNames: ["late"] },
    { label: "Not Acknowledged", icon: "fa-bell", color: "warning", domain: () => [["state", "in", ["purchase", "done"]], ["acknowledged", "=", false]], filterNames: ["not_acknowledged"] },
    { label: "Pending Approval", icon: "fa-hourglass-half", color: "warning", domain: () => [["state", "=", "to approve"]], filterNames: ["to_approve"] },
    { label: "Tender-Linked RFQs", icon: "fa-gavel", color: "primary", domain: () => [["govoo_tender_id", "!=", false], ["state", "in", ["draft", "sent"]]], filterNames: ["tender_linked"] },
];

export class GovooPurchaseKpiRenderer extends FileUploadListRenderer {
    static template = "govoo_procurement.PurchaseKpiRenderer";
    static components = {
        ...FileUploadListRenderer.components,
        GovooProcurementKpiStrip,
    };

    setup() {
        super.setup();
        this.kpiTiles = RFQ_TILES;
    }
}

registry.category("views").add("purchase_dashboard_list_govoo_kpi", {
    ...fileUploadListView,
    Controller: PurchaseFileUploadListController,
    Renderer: GovooPurchaseKpiRenderer,
});
