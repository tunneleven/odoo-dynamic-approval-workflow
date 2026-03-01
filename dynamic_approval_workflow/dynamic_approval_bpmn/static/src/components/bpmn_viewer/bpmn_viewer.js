/** @odoo-module **/

import { Component, onWillStart } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

/**
 * BpmnViewer — OWL 2 read-only runtime viewer with state overlays.
 *
 * SDS §5.2: Viewer with overlay engine for node-state CSS classes.
 * ADR-003: Lazy asset loading.
 *
 * Overlay state mapping:
 *   - o_daw_node_active
 *   - o_daw_node_completed
 *   - o_daw_node_pending
 *   - o_daw_node_error
 */
export class BpmnViewer extends Component {
    static template = "dynamic_approval_bpmn.BpmnViewer";
    static props = {
        bpmnXml: { type: String, optional: true },
        nodeStates: { type: Object, optional: true },
    };

    setup() {
        onWillStart(async () => {
            await loadJS("/dynamic_approval_bpmn/static/lib/bpmn-js/bpmn-navigated-viewer.development.js");
        });
    }
}
