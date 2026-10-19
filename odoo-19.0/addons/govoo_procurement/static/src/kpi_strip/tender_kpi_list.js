/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { GovooProcurementKpiStrip } from "./kpi_strip";

// The Tenders list had zero at-a-glance stats. Same js_class mechanism
// govoo_portal's list_kpi pattern uses (extend ListController, point it
// at a template that t-inherits "web.ListView" in "primary" mode).
// filterNames reference the named filters already added to
// view_govoo_tender_search (see views/govoo_tender_views.xml).
const TENDER_TILES = [
    { label: "Pre-Evaluation", icon: "fa-hourglass-start", color: "secondary", domain: () => [["evaluation_stage", "=", "pre_evaluation"]], filterNames: ["stage_pre_evaluation"] },
    { label: "Technical Evaluation", icon: "fa-search", color: "info", domain: () => [["evaluation_stage", "=", "technical_evaluation"]], filterNames: ["stage_technical_evaluation"] },
    { label: "Financial Evaluation", icon: "fa-calculator", color: "warning", domain: () => [["evaluation_stage", "=", "financial_evaluation"]], filterNames: ["stage_financial_evaluation"] },
    { label: "Awarded", icon: "fa-trophy", color: "success", domain: () => [["evaluation_stage", "=", "awarded"]], filterNames: ["stage_awarded"] },
];

export class GovooTenderKpiListController extends ListController {
    static template = "govoo_procurement.TenderKpiListView";
    static components = {
        ...ListController.components,
        GovooProcurementKpiStrip,
    };

    setup() {
        super.setup();
        this.kpiTiles = TENDER_TILES;
    }
}

registry.category("views").add("govoo_tender_kpi_list", {
    ...listView,
    Controller: GovooTenderKpiListController,
});
