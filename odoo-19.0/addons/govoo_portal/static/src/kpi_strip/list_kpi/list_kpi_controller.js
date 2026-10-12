/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { GovooListKpiStrip } from "./list_kpi_strip";

// Issue #261. A plain <widget> tag can't be dropped into a <list> arch the
// way it can into a regular form -- there is no equivalent slot for it --
// so each KPI-strip-carrying list view gets its own small js_class,
// following the exact pattern Odoo's own project_task_list view uses
// (extend ListController, point it at a template that t-inherits
// "web.ListView" in "primary" mode). All five views below share the SAME
// template (list_kpi_controller.xml) and component; only kpiTiles differs.
export class GovooKpiListController extends ListController {
    static template = "govoo_portal.KpiListView";
    static components = {
        ...ListController.components,
        GovooListKpiStrip,
    };
}

export function makeGovooKpiListController(tiles) {
    return class extends GovooKpiListController {
        setup() {
            super.setup();
            this.kpiTiles = tiles;
        }
    };
}
