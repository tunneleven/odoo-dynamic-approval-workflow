Dynamic Approval Workflow — BPMN Designer
==========================================

Provides BPMN diagram modeler and runtime viewer for the
Dynamic Approval Workflow suite.

This module bundles a ``bpmn-js`` based OWL 2 component for
drag-and-drop BPMN workflow authoring and a read-only runtime
viewer with state overlays.

**Key capabilities:**

* Drag-and-drop BPMN modeler using ``bpmn-js`` (OWL 2).
* Read-only runtime viewer with node-state overlays.
* BPMN XML import/export for supported subset.
* Validation of unsupported BPMN elements.
* Lazy asset loading — ``bpmn-js`` only loaded on first use.
* Compilation from BPMN XML to deterministic runtime metadata.

Install this module only if diagram authoring or runtime
visualization is required. ``dynamic_approval_core`` runs
independently without this module.

Architecture reference: ``ADR-001``, ``ADR-003``.
