# SRS-03 BPMN Modeling, Validation, and Viewer

Version: `v1.2-draft`
Date: `2026-03-01`
Parent: `dynamic_approval_workflow_srs_v1.3.md`
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define detailed requirements for BPMN authoring UX, validation behavior, canonical XML management, compile-metadata generation, and runtime diagram visualization.

## 2. Scope
In scope:
1. BPMN modeler behavior in workflow designer UI.
2. Supported BPMN subset and unsupported element handling.
3. Import/export contract for canonical BPMN XML.
4. Compile pipeline from canonical XML to runtime metadata.
5. Runtime viewer overlays for creators and approvers.

Out of scope:
1. Version lifecycle and activation precedence (`SRS-01`).
2. Runtime token execution semantics (`SRS-04`).
3. Human task lifecycle and approver actions (`SRS-05`).

## 3. Inherited Requirement Coverage
- FR: `FR-013..020`
- NFR: `NFR-009`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-03-001` | Workflow modeler UI shall use `bpmn-js` as the rendering and editing engine. | `FR-013` |
| `DFR-03-002` | Designer shall support drag-and-drop BPMN authoring with palette, direct editing, and property panel controls for supported subset. | `FR-014` |
| `DFR-03-003` | `bpmn_xml` shall be canonical source of truth; compiled metadata shall be a versioned derived artifact generated from canonical XML. | `FR-015` |
| `DFR-03-004` | Runtime diagram viewer shall use `bpmn-js` in read-only mode. | `FR-016` |
| `DFR-03-005` | Import/export shall support BPMN XML for the supported subset with deterministic canonicalization rules. | `FR-017` |
| `DFR-03-006` | Unsupported BPMN elements and invalid references shall produce structured validation errors including `element_id`, `element_type`, `xpath_location`, `error_category`, `error_code`, and `remediation_hint`. | `FR-018` |
| `DFR-03-007` | Creator and approver roles shall have runtime diagram visibility under access policy checks. | `FR-019` |
| `DFR-03-008` | Runtime viewer shall visualize current node, completed nodes, and pending approvers with deterministic overlay rules. | `FR-020` |
| `DFR-03-009` | Diagram viewer P95 load for standard-size flows (≤75 BPMN nodes including gateways) shall be under 1.5 seconds. | `NFR-009` |

## 5. Domain Objects (Conceptual)
1. `workflow.diagram.asset`
- Canonical BPMN XML and metadata fingerprint.
2. `workflow.diagram.validation_result`
- Validation errors/warnings and element references.
3. `workflow.diagram.compile_artifact`
- Runtime-ready derived metadata linked to canonical hash.
4. `workflow.diagram.viewer_state`
- Runtime overlay payload for role-aware visualization.

## 6. Supported BPMN Subset Contract
### 6.1 Supported Elements
1. Start event.
2. End event.
3. User task.
4. Exclusive gateway.
5. Parallel gateway.
6. Intermediate timer event.
7. Sequence flow.

### 6.2 Unsupported Elements
1. Unsupported elements are blocked at validation with explicit error code.
2. Unsupported element errors include:
- element ID
- element type
- location/path in diagram
- remediation hint

### 6.3 Deterministic Subset Rules
1. Every supported workflow must have one reachable start and at least one reachable terminal end path.
2. Gateway join behavior must be resolvable by runtime engine contracts in `SRS-04`.
3. Cross-reference IDs must be unique in canonical XML.

## 7. Modeler UX Contract
### 7.1 Authoring Behavior
1. Palette and drag-drop operations shall create syntactically valid BPMN nodes.
2. Property edits shall be persisted to canonical XML representation.
3. Undo/redo shall be supported within edit session scope.

### 7.2 Validation Feedback
1. Validation runs on demand and before publish handoff.
2. Errors are categorized: `structural`, `semantic`, `unsupported_element`, `reference_resolution`.
3. Modeler highlights error elements and shows structured messages.

### 7.3 Accessibility and Usability
1. Keyboard navigation shall be available for the following core operations: node selection, node deletion, undo, redo, zoom in/out, save, and validate.
2. Validation messages shall remain visible until acknowledged or corrected.

## 8. Import/Export and Compilation Contract
### 8.1 Import Rules
1. Imported XML is normalized to canonical formatting before save.
2. Non-supported elements are rejected with error report.
3. Import does not auto-publish or auto-activate definitions.

### 8.2 Export Rules
1. Exported XML equals canonical stored `bpmn_xml` (byte-for-byte after canonicalization policy).
2. Export metadata includes canonical hash and schema version.

### 8.3 Compilation Rules
1. Compile artifact generation is deterministic for same canonical XML and compiler version.
2. Compile artifact stores canonical hash reference.
3. Hash mismatch between compile artifact and canonical XML blocks publish/runtime load.

## 9. Runtime Viewer Contract
### 9.1 Visibility Rules
1. Creator and assigned approvers can access runtime viewer for authorized instances.
2. Unauthorized users receive access denied without revealing runtime state.

### 9.2 Overlay Semantics
1. Current active node is highlighted as `active`.
2. Completed nodes are marked `completed`.
3. Pending approvers for active tasks are listed in overlay side panel and linked to task state.
4. Rejected or cancelled paths are labeled with terminal reason code where available.

### 9.3 Performance Contract
1. Viewer payload must be optimized for initial render under `NFR-009` target.
2. Overlay refresh operations shall not perform full diagram reparse when only runtime state (node highlighting, approver list) changes; overlay updates shall be incremental.

### 9.4 Standard-Size Definition
1. "Standard-size flow" is defined as a BPMN diagram with at most 75 total BPMN nodes (tasks, gateways, events, and intermediate elements).
2. Diagrams exceeding 75 nodes are classified as "large" and may degrade below the P95 1.5-second target; performance for large diagrams is best-effort.
3. The 75-node threshold is subject to ops calibration during Phase 5 load testing and may be revised upward with evidence.

## 10. APIs and Events (Diagram Domain)
### 10.1 Logical Operations
1. `create_diagram_session(definition_key)`
2. `save_bpmn_xml(draft_id, bpmn_xml, expected_revision)`
3. `validate_bpmn_xml(draft_id)`
4. `import_bpmn_xml(draft_id, xml_payload)`
5. `export_bpmn_xml(version_id)`
6. `compile_bpmn_xml(version_id)`
7. `get_runtime_viewer_state(instance_id, actor)`

### 10.2 Required Audit Events
1. `workflow.diagram.edited`
2. `workflow.diagram.validated`
3. `workflow.diagram.imported`
4. `workflow.diagram.exported`
5. `workflow.diagram.compiled`
6. `workflow.diagram.viewer_accessed`

## 11. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-FR-013-001` | `FR-013` | Open modeler UI | `bpmn-js` modeler loads successfully |
| `TC-FR-014-001` | `FR-014` | Drag-and-drop supported elements into diagram | Diagram updates and persists valid XML |
| `TC-FR-015-001` | `FR-015` | Compile canonical XML | Versioned compile artifact generated and hash-linked |
| `TC-FR-016-001` | `FR-016` | Open runtime diagram viewer | `bpmn-js` viewer renders read-only runtime diagram |
| `TC-FR-017-001` | `FR-017` | Import supported BPMN XML and export it | Canonicalized import stored and export contract satisfied |
| `TC-FR-018-001` | `FR-018` | Import diagram with unsupported element | Structured validation error returned with location |
| `TC-FR-019-001` | `FR-019` | Creator and approver open same runtime diagram | Both roles can view according to access policy |
| `TC-FR-020-001` | `FR-020` | Runtime with active, completed, pending states | Viewer highlights active/completed and pending approvers correctly |
| `TC-NFR-009-001` | `NFR-009` | Render runtime diagram with ≤75 nodes | P95 initial load under 1.5 seconds |
| `TC-FR-018-003` | `FR-018` | Validate diagram with orphan gateway branch | Publish blocked with `semantic` validation error |
| `TC-FR-018-004` | `FR-018` | Import XML with duplicate element IDs | Import rejected with `structural` error |
| `TC-FR-019-002` | `FR-019` | Unauthorized user requests viewer | Access denied; no runtime overlay data returned |
| `TC-NFR-009-002` | `NFR-009` | Render diagram at 75-node boundary | P95 under 1.5s at standard-size limit |
| `TC-FR-018-002` | `FR-018` | Validate broken reference in XML | `reference_resolution` error emitted and element marked |
| `TC-FR-015-002` | `FR-015` | Compile artifact hash mismatch with canonical XML | Operation blocked with integrity incident |

## 12. Traceability Matrix
| Canonical ID | Covered Sections | Primary Tests |
|---|---|---|
| `FR-013` | 4, 7 | `TC-FR-013-001` |
| `FR-014` | 4, 7 | `TC-FR-014-001` |
| `FR-015` | 4, 8 | `TC-FR-015-001`, `TC-FR-015-002` |
| `FR-016` | 4, 9 | `TC-FR-016-001` |
| `FR-017` | 4, 8 | `TC-FR-017-001` |
| `FR-018` | 4, 6, 7 | `TC-FR-018-001`, `TC-FR-018-002` |
| `FR-019` | 4, 9 | `TC-FR-019-001` |
| `FR-020` | 4, 9 | `TC-FR-020-001` |
| `NFR-009` | 4, 9 | `TC-NFR-009-001` |

## 13. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-03-01` | Diagram with orphan gateway branch | Validation blocks publish handoff with semantic error | Tech Lead | `TC-FR-018-003` |
| `EC-03-02` | XML import with duplicate element IDs | Import rejected with `structural` error | Workflow Designer | `TC-FR-018-004` |
| `EC-03-03` | Viewer request by unauthorized user | Access denied; no runtime overlay leak | Security Lead | `TC-FR-019-002` |
| `EC-03-04` | Diagram with 75 nodes (standard-size boundary) | Performance P95 remains under 1.5s | Ops Lead | `TC-NFR-009-002` |

## 14. Sign-off Checklist
1. All inherited requirements in Section 3 are mapped in Section 12.
2. Unsupported element validation provides location and remediation context.
3. Canonical XML and compile artifact hash-link contract is explicit.
4. Runtime viewer overlay semantics align with `SRS-04` state model.
5. Access visibility constraints align with `SRS-07` security controls.

## 15. Open Issues
1. ~~Exact maximum "standard-size" diagram node count~~ — **RESOLVED**: defined as ≤75 BPMN nodes in §9.4; subject to ops recalibration in Phase 5.
2. Optional diff-view UX for diagram version comparison deferred to future enhancement.

## 16. Next Document
After approval of `SRS-03`, proceed to `srs_05_approver_resolution_human_tasks.md`.
