# SRS-03 Review Report: BPMN Modeling, Validation, and Viewer

**Reviewer:** AI Spec Reviewer
**Date:** 2026-02-28
**Review Iteration:** 1 (against `v1.1-draft`)
**Document Under Review:** `srs_03_bpmn_modeling_validation_viewer.md` (`v1.1-draft`, 2026-02-28)
**Baseline References:** `dynamic_approval_workflow_srs_v1.3.md`, `srs_00_master_traceability.md`

---

## Executive Summary

**Overall Assessment: CONDITIONALLY READY — Development can start on modeler/viewer core; important specification gaps remain**

SRS-03 covers all 9 canonical IDs (`FR-013..020`, `NFR-009`) with complete DFR decomposition, traceability matrix, and a clean domain model. The supported BPMN subset, canonical XML contract, compile pipeline, and runtime viewer overlay semantics are well-defined.

However, there are **0 Critical**, **5 Important**, and **6 Minor** gaps. The most significant issues are: (1) compile artifact schema and compile-to-runtime handoff contract are undefined, (2) edge-case tests remain "(planned)" and not promoted to the acceptance table, (3) `bpmn-js` integration specifics for Odoo 19 OWL are absent, and (4) the validation error schema lacks formalization. None require structural rework; all are precision items.

---

## 1. Requirement Coverage Verification

### 1.1 Canonical Mapping (PASS)

All assigned canonical IDs from SRS-00 §7 for SRS-03 are present in:
1. Section 3 — inherited scope
2. Section 4 — DFR table (9 DFRs mapping to 9 canonical IDs)
3. Section 12 — traceability matrix

No orphan DFR detected. No missing canonical ID.

### 1.2 Coverage Depth (PARTIAL)

| Canonical ID | Depth Assessment |
|---|---|
| `FR-013` | Adequate — modeler engine specified |
| `FR-014` | Adequate — drag-drop authoring, palette, property panel |
| `FR-015` | **Shallow** — compile pipeline stated but artifact schema undefined |
| `FR-016` | Adequate — viewer engine specified |
| `FR-017` | Adequate — import/export with canonicalization |
| `FR-018` | **Partial** — error categories listed but no structured error schema |
| `FR-019` | Adequate — role-based visibility |
| `FR-020` | Adequate — overlay semantics for active/completed/pending |
| `NFR-009` | **Partial** — target stated but benchmark profile undefined |

### 1.3 Cross-SRS Boundary References (PARTIAL)

| Boundary | Referenced? | Assessment |
|---|---|---|
| SRS-01 (version lifecycle) | Yes, in Scope | OK |
| SRS-04 (runtime token execution) | Yes, in Scope and §6.3 | **Handoff under-specified** — §6.3 says "Gateway join behavior must be resolvable by runtime engine contracts in SRS-04" but doesn't define the compile artifact → runtime metadata interface contract |
| SRS-05 (human tasks) | Yes, in Scope | OK |
| SRS-07 (access/security) | Yes, in §14 checklist | OK |
| SRS-10 (data model/API) | Not referenced | **Missing** — compile artifact schema and diagram asset data model should cross-reference SRS-10 |

---

## 2. Findings (Ordered by Severity)

### 2.1 Important Findings

| ID | Location | Finding | Impact | Recommendation |
|---|---|---|---|---|
| GAP-03-01 | §5.3, §8.3 | **Compile artifact schema undefined.** `workflow.diagram.compile_artifact` is listed as a domain object and §8.3 states compilation is deterministic with hash-linking, but the actual schema of the compile artifact (what fields, what structure, what the runtime engine consumes) is never specified. SRS-04 references "compiled condition metadata" but the handoff shape from SRS-03's compiler to SRS-04's runtime is not formalized in either document. | Developers cannot implement the compile pipeline without guessing the output format. SRS-04 runtime engine implementer has no contract to code against. | Define a compile artifact schema section specifying: output fields (node list, edge list, gateway semantics, condition references, task metadata), format (JSON), and version tag. Alternatively, defer to SRS-10 with explicit cross-reference, but SRS-10 must define it before SRS-03 compile work begins. |
| GAP-03-02 | §13 (EC register) | **4 edge-case tests remain "(planned)" and are not in §11 acceptance table.** `TC-FR-018-003`, `TC-FR-018-004`, `TC-FR-019-002`, `TC-NFR-009-002` are listed in the edge-case register but not promoted to the acceptance criteria table. Per SRS-00 §8.2, every acceptance criterion must reference explicit test IDs and compliance/security items must have negative-path tests. `TC-FR-019-002` (unauthorized access) is a security negative-path test that should be mandatory. | Traceability appears complete but actual test baseline is weaker than the register implies. Sign-off criteria from SRS-00 may not be met. | Promote all 4 planned tests into §11 acceptance table. At minimum, `TC-FR-019-002` (unauthorized viewer access) must be mandatory before sign-off. |
| GAP-03-03 | §7 | **`bpmn-js` integration with Odoo 19 OWL framework unspecified.** SRS-03 mandates `bpmn-js` for both modeler and viewer but never addresses: (a) how `bpmn-js` (vanilla JS/DOM library) integrates with Odoo 19's OWL component framework, (b) OWL component lifecycle management (mount/unmount/reactivity), (c) asset bundling strategy (npm package vs CDN vs vendored), (d) version pinning and update policy for `bpmn-js`. | Developers may choose incompatible integration patterns; OWL reactivity conflicts with `bpmn-js` internal DOM management could cause rendering bugs. | Add a "Technical Integration" subsection to §7 or a linked TDD covering: OWL wrapper component contract, `bpmn-js` version pin, asset bundling approach, and lifecycle hook mapping. |
| GAP-03-04 | §6.2, §7.2 | **Validation error schema not formalized.** §6.2 lists error fields (element ID, type, location, remediation hint) and §7.2 lists error categories (`structural`, `semantic`, `unsupported_element`, `reference_resolution`) but no structured error object schema is defined. Without a contract, frontend rendering of validation errors and backend error generation will diverge. | Inconsistent error handling between modeler UI and backend validation; integration testing becomes harder. | Define a validation error object schema: `{error_code, category, element_id, element_type, xpath_location, message, remediation_hint, severity}`. |
| GAP-03-05 | §10.1, §10.2 | **API operation input/output contracts undefined.** §10.1 lists 7 logical operations but provides no request/response schemas. Key gaps: (a) `validate_bpmn_xml` — what is the response format? List of error objects? (b) `get_runtime_viewer_state` — what fields in the viewer state payload? (c) `compile_bpmn_xml` — what does it return? | Frontend developers cannot implement modeler save/validate/compile flows without guessing API shapes. Viewer component cannot be built without knowing the overlay payload structure. | Define request/response schemas for at least `validate_bpmn_xml`, `compile_bpmn_xml`, and `get_runtime_viewer_state`. |

### 2.2 Minor Findings

| ID | Location | Finding | Impact | Recommendation |
|---|---|---|---|---|
| GAP-03-06 | §15 item 1 | **"Standard-size" benchmark undefined.** `NFR-009` requires P95 load under 1.5s for "standard-size flows" but the node count, edge count, and complexity profile are not defined. Open issue §15 acknowledges this but provides no target date or interim definition. | Performance testing is not reproducible; pass/fail criteria are subjective. | Define interim benchmark: e.g., "standard-size = up to 30 nodes, 40 edges, 5 gateways" with final calibration deferred to ops readiness. |
| GAP-03-07 | §8.1, §8.2 | **XML canonicalization policy not specified.** §8.1 says "normalized to canonical formatting" and §8.2 says "byte-for-byte after canonicalization policy" but the canonicalization rules (whitespace handling, attribute ordering, namespace normalization, encoding) are never defined. | Hash-linked compile artifacts may produce false mismatches due to non-deterministic XML serialization; import/export round-trip may fail byte-comparison. | Specify canonicalization rules: XML C14N variant, encoding (UTF-8), attribute sort order, whitespace policy. |
| GAP-03-08 | §7.3 | **Accessibility requirements too vague.** §7.3 says "Keyboard navigation for core operations shall be available" without defining which operations, keyboard shortcuts, or WCAG level target. | Untestable requirement; accessibility audit scope is undefined. | Specify minimum: WCAG 2.1 AA for modeler controls, list core keyboard-navigable operations (add node, delete, navigate, undo/redo, validate). |
| GAP-03-09 | §9.2 | **Overlay refresh mechanism undefined.** §9.3 says "Overlay refresh operations should avoid full diagram reparse when only runtime state changes" but doesn't specify: polling interval, WebSocket/SSE push, or manual refresh. | Viewer may show stale state; developers choose different refresh strategies leading to inconsistent UX. | Specify refresh mechanism: polling with configurable interval (default 30s) or server-push via Odoo bus, with manual refresh always available. |
| GAP-03-10 | §8 | **No XML schema version policy.** §8.2 includes "schema version" in export metadata but there's no schema evolution policy: what happens when a new `bpmn-js` version or a new supported element is added? Can older XML be loaded in newer versions? | Forward/backward compatibility issues when upgrading; old diagrams may fail validation silently. | Add schema version compatibility rules: older versions loadable in newer engine with migration warnings; newer versions blocked in older engine with explicit error. |
| GAP-03-11 | §9, §10 | **Multi-company isolation for diagram assets unstated.** Parent SRS `FR-079` requires multi-company isolation for "diagram visibility." SRS-03 §9.1 mentions "authorized instances" but doesn't explicitly state company-scoped access for diagram assets and compile artifacts. | Cross-company data leak in multi-tenant deployments. | Add explicit company isolation rule: diagram assets, compile artifacts, and viewer state are company-scoped; cross-company access denied. Reference SRS-07 §8 isolation rules. |

---

## 3. Edge Case Coverage Assessment

### 3.1 Covered Edge Cases

| EC ID | Edge Case | Test Coverage |
|---|---|---|
| EC-03-01 | Orphan gateway branch | `TC-FR-018-003` (planned — not in §11) |
| EC-03-02 | Duplicate element IDs in import | `TC-FR-018-004` (planned — not in §11) |
| EC-03-03 | Unauthorized viewer access | `TC-FR-019-002` (planned — not in §11) |
| EC-03-04 | Near-limit standard-size diagram | `TC-NFR-009-002` (planned — not in §11) |

### 3.2 Missing Edge Cases

| ID | Missing Edge Case | Risk | Recommendation |
|---|---|---|---|
| EC-M1 | **Concurrent editing of same diagram by two designers.** No locking, conflict detection, or last-write-wins policy defined. | Data loss: one user's changes silently overwritten. | Define concurrency control: pessimistic lock (edit session claim) or optimistic lock (`expected_revision` on save — already in API but not elaborated). Add test. |
| EC-M2 | **Diagram with circular gateway paths (infinite loop).** Exclusive gateway with condition always true looping back. | Compile may succeed but runtime enters infinite loop (SRS-04 concern, but validation should catch it). | Add compile-time cycle detection validation rule in §6.3 or §8.3. Cross-reference SRS-04 loop-detection contract. |
| EC-M3 | **Very large diagram exceeding standard-size.** No upper limit defined; user creates diagram with 200+ nodes. | Catastrophic performance degradation; browser tab crash; server timeout on compile. | Define hard upper limit (e.g., 100 nodes max) with validation error, and soft warning threshold (e.g., 50 nodes). |
| EC-M4 | **`bpmn-js` library fails to load (CDN down, asset bundle error).** | Modeler and viewer are completely non-functional; no fallback. | Define fallback behavior: graceful error message, retry mechanism, and offline asset bundle strategy. |
| EC-M5 | **Compile artifact exists but canonical XML is later modified without recompile.** Hash mismatch detected at runtime. | §8.3 item 3 says "hash mismatch blocks publish/runtime load" but no test exists for this scenario beyond `TC-FR-015-002`. No specification of what happens to in-flight instances using the old compile artifact. | Clarify that in-flight instances continue with their pinned compile artifact; only new instance starts are blocked. Add test. |
| EC-M6 | **Import of valid BPMN XML that uses supported elements but has semantic conflicts with existing definition.** E.g., imported diagram references task IDs that conflict with another version's task IDs. | Silent overwrite of task metadata; broken version history. | Define import isolation: imported XML is treated as new draft; no automatic merge with existing versions. |
| EC-M7 | **Undo/redo stack overflow.** §7.1 item 3 says undo/redo within session scope but no stack depth limit or memory bound. | Memory exhaustion on long editing sessions with many operations. | Define maximum undo stack depth (e.g., 100 operations) with oldest entries dropped. |
| EC-M8 | **Runtime viewer for cancelled/rejected instance.** §9.2 item 4 mentions "rejected or cancelled paths" but no test covers viewer behavior for fully terminated instances. | Viewer may show stale "active" overlays for terminated instances. | Add test: viewer for terminal-rejected instance shows final state with no active highlights. |

---

## 4. Cross-SRS Boundary Assessment

| Boundary | Status | Detail |
|---|---|---|
| **SRS-03 ↔ SRS-01** | OK | Scope correctly defers version lifecycle. Diagram assets are linked to definition versions per SRS-01 contract. |
| **SRS-03 ↔ SRS-04** | **Needs clarification** | Compile artifact is the bridge between SRS-03 (authoring) and SRS-04 (runtime). Neither document defines the compile artifact schema or the interface contract. §6.3 item 2 says "Gateway join behavior must be resolvable by runtime engine contracts in SRS-04" but the actual data shape is unspecified. SRS-04 references "compiled condition metadata" without linking to SRS-03's compiler output. |
| **SRS-03 ↔ SRS-05** | OK | Correctly defers human task lifecycle. Viewer overlay shows pending approvers but task details are SRS-05 domain. |
| **SRS-03 ↔ SRS-07** | Partial | Sign-off checklist item 5 references SRS-07. But `FR-079` (multi-company isolation for diagrams) is not explicitly addressed in SRS-03 body text. See GAP-03-11. |
| **SRS-03 ↔ SRS-10** | **Not referenced** | Compile artifact data model, diagram asset storage schema, and validation error schema should be cross-referenced to SRS-10. Currently no link exists. |

---

## 5. Strengths

1. **Clean BPMN subset definition** (§6) — supported/unsupported element contract is clear and actionable; error reporting includes element-level context.
2. **Canonical XML as source of truth** (§8) — compile-from-canonical with hash-linking prevents metadata drift and ensures deterministic builds.
3. **Runtime viewer overlay semantics** (§9.2) — active/completed/pending/rejected state mapping is deterministic and role-aware.
4. **Complete traceability** (§12) — all 9 canonical IDs mapped with primary tests; no orphan DFRs.
5. **Separation of authoring and viewing** — modeler (design-time) and viewer (runtime) are cleanly separated with distinct API operations.
6. **Good validation categorization** (§7.2) — four error categories provide a solid foundation for structured error handling.
7. **Audit event coverage** (§10.2) — 6 audit events cover the full diagram lifecycle from edit to viewer access.

---

## 6. Prioritized Action Plan

| Priority | ID | Action | Effort |
|---|---|---|---|
| P1 | GAP-03-01 | Define compile artifact schema (output fields, format, version tag) or cross-reference SRS-10 | 1.5h |
| P1 | GAP-03-02 | Promote 4 planned edge-case tests to §11 acceptance table | 0.5h |
| P1 | GAP-03-03 | Add `bpmn-js` / Odoo 19 OWL technical integration section or TDD reference | 1.0h |
| P1 | GAP-03-04 | Formalize validation error object schema | 0.5h |
| P1 | GAP-03-05 | Define request/response schemas for key API operations | 1.0h |
| P2 | GAP-03-06 | Define interim "standard-size" benchmark profile with node/edge counts | 0.25h |
| P2 | GAP-03-07 | Specify XML canonicalization rules (C14N variant, encoding, whitespace) | 0.25h |
| P2 | GAP-03-08 | Specify accessibility scope (WCAG level, keyboard operations) | 0.25h |
| P2 | GAP-03-09 | Define viewer overlay refresh mechanism (polling/push/manual) | 0.25h |
| P2 | GAP-03-10 | Add XML schema version compatibility policy | 0.25h |
| P2 | GAP-03-11 | Add explicit multi-company isolation rules for diagram assets | 0.25h |
| P2 | EC-M1–M8 | Add 8 missing edge cases to register with linked test IDs | 1.0h |

**Total estimated effort:** ~7.0 hours

---

## 7. Verdict

**SRS-03 v1.1-draft is structurally sound with complete canonical coverage.**

Development can begin on the `bpmn-js` modeler UI shell, supported element palette, and basic viewer rendering. However, **compile pipeline implementation is blocked** until GAP-03-01 (compile artifact schema) is resolved — either inline in SRS-03 or via SRS-10. Frontend integration work requires GAP-03-03 (OWL integration pattern) to avoid rework.

**Recommended path to sign-off:**
1. Resolve the 5 Important items (GAP-03-01 through GAP-03-05).
2. Add the 8 missing edge cases (EC-M1 through EC-M8) to the register.
3. Address the 6 Minor items as time permits (none are blocking).
4. Coordinate with SRS-04 on compile artifact → runtime metadata interface contract.
5. Rerun traceability and test completeness check.
6. Proceed to sign-off.
