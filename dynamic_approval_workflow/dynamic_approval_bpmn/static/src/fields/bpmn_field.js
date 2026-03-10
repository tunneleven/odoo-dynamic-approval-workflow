/** @odoo-module **/

import { registry } from "@web/core/registry";
import { BpmnModelerComponent } from "../components/bpmn_modeler/bpmn_modeler";

/**
 * BpmnField — form field widget for inline BPMN display.
 *
 * OMB-05 §3.3: Registers the `bpmn_xml` widget in the fields registry.
 * Renders BpmnModeler in edit mode. In readonly mode, the modeler component
 * disables interaction (future: switch to BpmnViewer per OMB-05 §3.2).
 */

registry.category("fields").add("bpmn_xml", {
    component: BpmnModelerComponent,
    supportedTypes: ["text"],
});
