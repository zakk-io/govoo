/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// Issue #261: generic KPI strip for a plain list view (Meetings, Resolutions,
// Contracts, Obligations, Compliance Instances). Unlike the dashboard's
// GovooKpiStrip (kpi_strip.js), every tile here queries the SAME model the
// page is already showing -- whoever can open the page already has read
// access to that model, so (unlike the dashboard's cross-model strip) no
// per-tile access-rights gating is needed. Counts are always global for the
// model (ignoring the list's own current search/filter state), matching the
// dashboard KPI strip's behaviour.
export class GovooListKpiStrip extends Component {
    static template = "govoo_portal.ListKpiStrip";
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
