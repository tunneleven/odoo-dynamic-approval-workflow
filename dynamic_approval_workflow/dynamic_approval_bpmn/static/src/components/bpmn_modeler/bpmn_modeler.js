/** @odoo-module **/

import { Component, onWillStart } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

/**
 * BpmnModeler — OWL 2 component wrapping bpmn-js for diagram authoring.
 *
 * SDS §5.2: Modeler component with palette, drag-drop, property panel.
 * ADR-003: Lazy asset loading via loadJS on first mount.
 *
 * Supported BPMN subset:
 *   Start Event, End Event, User Task, Exclusive Gateway,
 *   Parallel Gateway, Intermediate Timer Event, Sequence Flow.
 */
export class BpmnModeler extends Component {
    static template = "dynamic_approval_bpmn.BpmnModeler";
    static props = {
        bpmnXml: { type: String, optional: true },
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        onWillStart(async () => {
            await loadJS("/dynamic_approval_bpmn/static/lib/bpmn-js/bpmn-modeler.development.js");
        });
    }
}
