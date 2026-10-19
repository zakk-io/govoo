/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// Generic KPI strip for a plain list view (Tenders, Requests for
// Quotation), matching the Clagov Dashboard's own card style (icon,
// colour-coded left border, clickable). Scoped to this module rather
// than reusing govoo_portal's identical component, since
// govoo_procurement has no dependency on govoo_portal.
export class GovooProcurementKpiStrip extends Component {
    static template = "govoo_procurement.KpiStrip";
    static props = {
        tiles: { type: Array },
        resModel: { type: String },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loading: true, counts: [] });
        onWillStart(() => this.loadCounts());
    }

    async loadCounts() {
        this.state.counts = await Promise.all(
            this.props.tiles.map((tile) => this.orm.searchCount(this.props.resModel, tile.domain()))
        );
        this.state.loading = false;
    }

    openTile(tile) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: tile.label,
            res_model: this.props.resModel,
            view_mode: "list,form",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: tile.domain(),
        });
    }
}
