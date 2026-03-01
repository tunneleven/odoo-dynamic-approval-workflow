# SRS-00 Master and Traceability

Version: `v1.1-draft`  
Date: `2026-03-01`  
Parent: `dynamic_approval_workflow_srs_v1.3.md`  
Directory: `addons-custom/dynamic_approval_workflow/docs/srs`
Glossary: `supplementary/portfolio_glossary.md`

## 1. Purpose
Define the governance and traceability contract for the Dynamic Approval Workflow SRS decomposition set. This document is the control point for:
1. Requirement ownership and mapping.
2. Requirement ID policy and lifecycle.
3. Requirement-to-document and requirement-to-test traceability.
4. Change control and sign-off rules.

## 2. Scope
In scope:
1. All `FR-*` and `NFR-*` inherited from parent SRS `v1.3`.
2. All detailed child SRS documents `SRS-01` to `SRS-10`.
3. Document lifecycle controls from draft to approved baseline.
4. Portfolio glossary governance (`supplementary/portfolio_glossary.md`).

Out of scope:
1. Detailed functional behavior (covered in child SRS files).
2. Implementation code design (covered in technical design and module docs).

## 3. Source of Truth and Precedence
1. Canonical functional/non-functional requirement IDs are defined in `dynamic_approval_workflow_srs_v1.3.md`.
2. `SRS-00` governs decomposition, mapping, and approval workflow.
3. Child SRS files elaborate behavior and acceptance criteria but must not contradict parent requirement intent.
4. If contradiction exists, implementation is blocked until a formal change request updates affected documents.

## 4. Portfolio and Ownership
| Doc ID | File | Domain | Primary Owner | Supporting Owners |
|---|---|---|---|---|
| `SRS-00` | `srs_00_master_traceability.md` | Governance and traceability | Product Owner | BA, Tech Lead, QA Lead |
| `SRS-01` | `srs_01_workflow_definition_versioning.md` | Definition/versioning | BA | Tech Lead, QA Lead |
| `SRS-02` | `srs_02_binding_enforcement_callback.md` | Binding/enforcement/callback | Tech Lead | BA, QA Lead |
| `SRS-03` | `srs_03_bpmn_modeling_validation_viewer.md` | BPMN modeler/viewer | Tech Lead | UX, QA Lead |
| `SRS-04` | `srs_04_runtime_orchestration_conditions.md` | Runtime orchestration | Tech Lead | BA, QA Lead |
| `SRS-05` | `srs_05_approver_resolution_human_tasks.md` | Approvers and tasks | BA | Tech Lead, QA Lead |
| `SRS-06` | `srs_06_signature_evidence_policy.md` | Signature and evidence | Compliance Lead | BA, Tech Lead |
| `SRS-07` | `srs_07_access_security_governance.md` | Access/security/governance | Security Lead | Tech Lead, QA Lead |
| `SRS-08` | `srs_08_notifications_webhooks_external_contracts.md` | Notifications/integration | Integration Lead | Tech Lead, QA Lead |
| `SRS-09` | `srs_09_operations_monitoring_retention_reliability.md` | Ops/reliability/retention | Ops Lead | Tech Lead, QA Lead |
| `SRS-10` | `srs_10_data_model_api_test_traceability.md` | Data/API/test traceability | Tech Lead | DBA, QA Lead |

## 5. Requirement ID Management Policy
## 5.1 Canonical IDs
1. Parent IDs are immutable keys: `FR-001..FR-096` (with reserved gaps) and `NFR-001..NFR-017`.
2. IDs must never be reused for a different semantic meaning.
3. Deprecated requirements keep their IDs and status; they are not deleted.

## 5.2 Child-Level Detail IDs
1. Child SRS files may define detailed derived requirements using format `DFR-<SRS>-<NNN>` (example: `DFR-02-001`).
2. Every `DFR-*` must map to at least one canonical `FR-*` or `NFR-*`.
3. No standalone `DFR-*` without canonical mapping is allowed.

## 5.3 Requirement Status
Allowed status values:
1. `proposed`
2. `approved`
3. `implemented`
4. `verified`
5. `deprecated`

## 6. Requirement Index Baseline
## 6.1 Coverage Summary (Parent v1.3)
1. Canonical FR count: `95` IDs (`FR-001..FR-096`, with `FR-080` currently unused/reserved).
2. Canonical NFR count: `17` IDs (`NFR-001..NFR-017`).
3. Target traceability completeness: `100%` canonical ID coverage across child SRS and tests.

## 6.2 FR Index by Capability Domain
| Capability Domain | Canonical IDs | Target Child SRS |
|---|---|---|
| Workflow definition and versioning | `FR-001..006`, `FR-066`, `FR-075`, `FR-086..089` | `SRS-01` |
| Binding, runtime integration, callback | `FR-007..012`, `FR-071`, `FR-072`, `FR-081`, `FR-090..095` | `SRS-02` |
| BPMN modeling and UX | `FR-013..020` | `SRS-03` |
| Routing/conditions/execution | `FR-021..028`, `FR-073`, `FR-082` | `SRS-04` |
| Approver resolution and human tasks | `FR-029..042`, `FR-074` | `SRS-05` |
| Signature and evidence policy | `FR-043..046`, `FR-084`, `FR-085`, `FR-096` | `SRS-06` |
| Followers | `FR-047..050` | `SRS-05` |
| Access/security/governance | `FR-051..055`, `FR-061..065`, `FR-079` | `SRS-07` |
| Notifications and webhooks | `FR-056..060`, `FR-083` | `SRS-08` |
| Operations and retention | `FR-067..070`, `FR-076..078` | `SRS-09` |
| Cross-contract and traceability controls | Contract sections + test strategy references | `SRS-10` |

## 6.3 NFR Index by Domain
| NFR Domain | Canonical IDs | Target Child SRS |
|---|---|---|
| Availability, capacity, resilience | `NFR-001`, `NFR-003`, `NFR-013` | `SRS-09` |
| Runtime consistency/latency | `NFR-002`, `NFR-004` | `SRS-04` |
| Integration idempotency | `NFR-005` | `SRS-08` |
| Evidence and retention | `NFR-006` | `SRS-06`, `SRS-09` |
| Isolation and security | `NFR-007`, `NFR-010`, `NFR-012` | `SRS-07` |
| Version stability | `NFR-008` | `SRS-01` |
| Diagram and UI integration | `NFR-009`, `NFR-011` | `SRS-03`, `SRS-02` |
| Mobile and localization | `NFR-014`, `NFR-015` | `NFR-014`: `SRS-05`; `NFR-015`: `SRS-09` |
| Idempotent mutation semantics | `NFR-016` | `SRS-10` |
| Cross-channel enforcement | `NFR-017` | `SRS-02` |

## 7. Requirement-to-Document Matrix (Control View)
| Canonical Requirement Group | Child SRS | Coverage Rule |
|---|---|---|
| `FR-001..006`, `FR-066`, `FR-075`, `FR-086..089`, `NFR-008` | `SRS-01` | Full ownership |
| `FR-007..012`, `FR-071`, `FR-072`, `FR-081`, `FR-090..095`, `NFR-011`, `NFR-017` | `SRS-02` | Full ownership |
| `FR-013..020`, `NFR-009` | `SRS-03` | Full ownership |
| `FR-021..028`, `FR-073`, `FR-082`, `NFR-002`, `NFR-004` | `SRS-04` | Full ownership |
| `FR-029..042`, `FR-047..050`, `FR-074`, `NFR-014` | `SRS-05` | Full ownership |
| `FR-043..046`, `FR-084`, `FR-085`, `FR-096`, `NFR-006` | `SRS-06` | Full ownership |
| `FR-051..055`, `FR-061..065`, `FR-079`, `NFR-007`, `NFR-010`, `NFR-012` | `SRS-07` | Full ownership |
| `FR-056..060`, `FR-083`, `NFR-005` | `SRS-08` | Full ownership |
| `FR-067..070`, `FR-076..078`, `NFR-001`, `NFR-003`, `NFR-013`, `NFR-015` | `SRS-09` | Full ownership |
| Contract/API/data/test traceability controls, `NFR-016` | `SRS-10` | Cross-cutting ownership |

## 8. Requirement-to-Test Traceability Rules
## 8.1 Test ID Convention
1. Functional tests: `TC-FR-<ID>-<NNN>` (example: `TC-FR-008-001`).
2. Non-functional tests: `TC-NFR-<ID>-<NNN>` (example: `TC-NFR-003-002`).
3. Cross-requirement scenario tests: `TC-X-<SRS>-<NNN>`.

## 8.2 Mandatory Mapping Rules
1. Every canonical `FR-*` and `NFR-*` must map to at least one test case.
2. Compliance/security requirements (`signature`, `access`, `audit`, `isolation`) must have both positive and negative-path tests.
3. Every child SRS acceptance criterion must reference explicit test IDs.
4. Release candidate cannot be approved with any unmapped canonical requirement.

## 8.3 Evidence Requirements
1. Each test execution record must include environment, build/version, timestamp, and result.
2. Failed tests must include defect/incident reference.
3. Requirement coverage report must be generated per release.

## 9. Change Control Workflow
## 9.1 Change Types
1. `minor`: wording clarification, no behavior change.
2. `major`: behavioral change within approved scope.
3. `breaking`: behavior, contract, or compliance-impacting change.

## 9.2 Workflow
1. Raise change request (`CR`) with rationale, impacted IDs, and proposed text.
2. Impact assessment by BA + Tech Lead + QA Lead (and Compliance/Security for regulated/security items).
3. Update impacted SRS documents and traceability matrix.
4. Re-baseline test mappings for impacted IDs.
5. Obtain sign-off per Section 10.
6. Publish new document version with change log entry.

## 10. Approval and Sign-off Workflow
## 10.1 Entry Criteria for Sign-off
1. Parent-to-child mapping is complete and conflict-free.
2. Every requirement in scope has acceptance criteria.
3. Every acceptance criterion references test IDs.

## 10.2 Sign-off Matrix
| Change Area | Required Approvers |
|---|---|
| Functional behavior | Product Owner, Tech Lead, QA Lead |
| Security/access | Security Lead, Tech Lead, QA Lead |
| Signature/compliance evidence | Compliance Lead, Product Owner, Tech Lead |
| API/webhook contract | Integration Lead, Tech Lead, QA Lead |
| Ops/SLO/retention | Ops Lead, Tech Lead, QA Lead |

## 10.3 Exit Criteria
1. Sign-off approvals recorded.
2. Traceability report shows `100%` canonical requirement mapping to child SRS and test IDs.
3. Updated baseline version is published in this directory.

## 11. Next Step
Draft `SRS-01` in detail using this traceability contract as the baseline.
