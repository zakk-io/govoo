/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// Generic KPI strip for a plain list view (Tenders, Requests for
// Quotation), matching the Clagov Dashboard's own card style (icon,
// colour-coded left border, clickable). Scoped to this module rather
// than reusing govoo_portal's identical component, since
// govoo_procurement has no dependency on govoo_portal.
//
// Each tile's filterNames must name an existing <filter> in the current
// list's own search view. Clicking a tile toggles that filter in place
// (same mechanism as Odoo's own native purchase dashboard cards,
// PurchaseDashBoard.setSearchContext) rather than opening a brand new
// action: a doAction() here was confirmed live to drop the user onto a
// bare, title-less action and lose the page's own search view/menu
// context entirely, instead of just filtering the page they're already on.
export class GovooProcurementKpiStrip extends Component {
    static template = "govoo_procurement.KpiStrip";
    static props = {
        tiles: { type: Array },
        resModel: { type: String },
    };

    setup() {
        this.orm = useService("orm");
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
        const searchModel = this.env.searchModel;
        const searchItems = searchModel.getSearchItems((item) => tile.filterNames.includes(item.name));
        searchModel.query = [];
        for (const item of searchItems) {
            searchModel.toggleSearchItem(item.id);
        }
    }
}
