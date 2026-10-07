/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { BoardController } from "@board/board_controller";
import { GovooKpiStrip } from "./kpi_strip";

// Mounts GovooKpiStrip into board.board's own BoardController (see
// kpi_strip.js for why a plain <widget> tag in the arch can't do this).
// Scoped to ONLY our two governance dashboard views -- not every
// board.board page in the database, which would otherwise also include
// Odoo's stock, unrelated "My Dashboard" (any user can have one via
// "Add to Dashboard" elsewhere in the app) -- by reading a marker class
// directly off the raw arch XML (<board class="o_govoo_board_dashboard">),
// which BoardArchParser itself ignores, so this costs no extra RPC
// roundtrip and can't leak onto a dashboard that isn't ours.
patch(BoardController.components, { GovooKpiStrip });

patch(BoardController.prototype, {
    setup() {
        super.setup();
        this.showGovooKpiStrip = Boolean(
            this.props.arch.querySelector("board.o_govoo_board_dashboard")
        );
    },
});
