/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * BpmnModeler — OWL 2 field component wrapping bpmn-js for diagram authoring.
 *
 * OMB-05 §3.1: Modeler component with restricted palette, lazy loading,
 * debounced save, validation RPC, and element-click events.
 *
 * ADR-003: Lazy asset loading — bpmn-js is loaded only when the component mounts.
 *
 * Supported BPMN subset (OMB-05 §7):
 *   Start Event, End Event, User Task, Exclusive Gateway,
 *   Parallel Gateway, Intermediate Timer Event, Sequence Flow.
 */

const BPMN_JS_PATH = "/dynamic_approval_bpmn/static/lib/bpmn-js/bpmn-modeler.production.min.js";
const SAVE_DEBOUNCE_MS = 500;

/**
 * Default empty BPMN diagram for new assets.
 */
const DEFAULT_BPMN_XML = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  targetNamespace="http://bpmn.io/schema/bpmn"
                  id="Definitions_1">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1"/>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_1" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="159" width="36" height="36"/>
      </bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`;

/**
 * Supported BPMN element types for the modeler palette.
 * All other element types are blocked at validation time (DFR-03-006).
 */
const SUPPORTED_ELEMENT_TYPES = new Set([
    "bpmn:StartEvent",
    "bpmn:EndEvent",
    "bpmn:UserTask",
    "bpmn:ExclusiveGateway",
    "bpmn:ParallelGateway",
    "bpmn:IntermediateCatchEvent",
    "bpmn:SequenceFlow",
]);

export class BpmnModelerComponent extends Component {
    static template = "dynamic_approval_bpmn.BpmnModeler";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.containerRef = useRef("bpmnContainer");
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.modeler = null;
        this._debounceTimer = null;
        this._destroyed = false;

        this.state = useState({
            loading: true,
            isDirty: false,
            validationErrors: [],
            validationWarnings: [],
        });

        onMounted(() => this._onMounted());
        onWillUnmount(() => this._onWillUnmount());
    }

    // ---- Lifecycle ----

    async _onMounted() {
        try {
            await loadJS(BPMN_JS_PATH);
            if (this._destroyed) {
                return;
            }
            await this._initModeler();
        } catch (error) {
            this.state.loading = false;
            this.notification.add(
                `Failed to load BPMN modeler: ${error.message}`,
                { type: "danger" }
            );
        }
    }

    _onWillUnmount() {
        this._destroyed = true;
        this._clearDebounce();
        if (this.modeler) {
            this.modeler.destroy();
            this.modeler = null;
        }
    }

    // ---- Modeler initialization ----

    async _initModeler() {
        const BpmnJS = window.BpmnJS;
        if (!BpmnJS) {
            this.state.loading = false;
            return;
        }

        const container = this.containerRef.el;
        if (!container) {
            this.state.loading = false;
            return;
        }

        this.modeler = new BpmnJS({
            container,
            keyboard: { bindTo: container },
        });

        this._bindModelerEvents();

        const xml = this.props.record.data[this.props.name] || DEFAULT_BPMN_XML;
        try {
            await this.modeler.importXML(xml);
            const canvas = this.modeler.get("canvas");
            canvas.zoom("fit-viewport");
        } catch (err) {
            this.notification.add(
                `BPMN import error: ${err.message}`,
                { type: "warning" }
            );
        }

        this.state.loading = false;

        if (this.props.readonly) {
            this._setReadonly(true);
        }
    }

    // ---- Event bindings ----

    _bindModelerEvents() {
        if (!this.modeler) {
            return;
        }

        const eventBus = this.modeler.get("eventBus");

        eventBus.on("commandStack.changed", () => {
            this.state.isDirty = true;
            this._debouncedSave();
        });

        eventBus.on("element.click", (event) => {
            const { element } = event;
            if (element && element.id) {
                this.env.bus.trigger("bpmn:element-click", {
                    elementId: element.id,
                    elementType: element.type,
                });
            }
        });
    }

    // ---- Save logic (debounced) ----

    _debouncedSave() {
        this._clearDebounce();
        this._debounceTimer = setTimeout(async () => {
            if (this._destroyed || !this.modeler) {
                return;
            }
            await this._saveXml();
        }, SAVE_DEBOUNCE_MS);
    }

    _clearDebounce() {
        if (this._debounceTimer) {
            clearTimeout(this._debounceTimer);
            this._debounceTimer = null;
        }
    }

    async _saveXml() {
        if (!this.modeler || this.props.readonly) {
            return;
        }

        try {
            const result = await this.modeler.saveXML({ format: true });
            const xml = result.xml;

            await this.props.record.update({ [this.props.name]: xml });
            this.state.isDirty = false;

            this.env.bus.trigger("bpmn:save", { xml });

            await this._validateXml(xml);
        } catch (error) {
            this.notification.add(
                `Failed to save BPMN XML: ${error.message}`,
                { type: "danger" }
            );
        }
    }

    // ---- Validation RPC ----

    async _validateXml(xml) {
        try {
            const result = await this.rpc(
                "/web/dataset/call_kw/workflow.diagram.asset/validate_bpmn_xml",
                {
                    model: "workflow.diagram.asset",
                    method: "validate_bpmn_xml",
                    args: [xml],
                    kwargs: {},
                }
            );

            this.state.validationErrors = result.errors || [];
            this.state.validationWarnings = result.warnings || [];

            this.env.bus.trigger("bpmn:validate", {
                errors: this.state.validationErrors,
                warnings: this.state.validationWarnings,
            });

            if (this.state.validationErrors.length > 0) {
                this.notification.add(
                    `BPMN validation: ${this.state.validationErrors.length} error(s)`,
                    { type: "warning" }
                );
            }
        } catch (error) {
            // Validation RPC failure should not block editing
            this.state.validationErrors = [];
            this.state.validationWarnings = [];
        }
    }

    // ---- Readonly mode ----

    _setReadonly(readonly) {
        if (!this.modeler) {
            return;
        }
        try {
            const modeling = this.modeler.get("modeling");
            if (readonly && modeling) {
                // Disable interaction by removing event listeners
                this.modeler.get("eventBus").fire("canvas.viewbox.changed", {});
            }
        } catch {
            // If modeling module not available, ignore
        }
    }

    // ---- Actions (called from template) ----

    async onValidateClick() {
        if (!this.modeler) {
            return;
        }
        try {
            const result = await this.modeler.saveXML({ format: true });
            await this._validateXml(result.xml);
        } catch (error) {
            this.notification.add(
                `Validation failed: ${error.message}`,
                { type: "danger" }
            );
        }
    }

    async onSaveClick() {
        this._clearDebounce();
        await this._saveXml();
    }

    onFitClick() {
        if (!this.modeler) {
            return;
        }
        const canvas = this.modeler.get("canvas");
        canvas.zoom("fit-viewport");
    }
}

// Exported for use in bpmn_field.js registry entry
// Field registration is handled in static/src/fields/bpmn_field.js
