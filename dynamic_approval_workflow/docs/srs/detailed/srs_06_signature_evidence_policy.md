# SRS-06 Signature and Evidence Policy

Version: `v1.2-draft`
Date: `2026-03-01`
Parent: `dynamic_approval_workflow_srs_v1.3.md`
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define detailed requirements for signature-required approvals, evidence immutability, system attestation behavior, legal human-signature constraints, and audit/report distinction.

## 2. Scope
In scope:
1. Signature-required step policy model.
2. Evidence taxonomy and immutable evidence fields.
3. Human signature vs system attestation semantics.
4. Timeout interactions with signature policy.
5. Audit/report representation requirements.
6. Retention policy hooks for signature evidence.

Out of scope:
1. Task lifecycle mechanics (`SRS-05`).
2. Runtime orchestration engine internals (`SRS-04`).
3. Physical storage retention execution (`SRS-09`).

## 3. Inherited Requirement Coverage
- FR: `FR-043..046`, `FR-084`, `FR-085`, `FR-096`
- NFR: `NFR-006`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-06-001` | Each step shall support optional `sign_required` policy to require signature evidence before completion. | `FR-043` |
| `DFR-06-002` | Steps with `sign_required = true` shall reject signed completion unless required evidence artifact exists and passes integrity checks. | `FR-044` |
| `DFR-06-003` | Evidence records shall be immutable and include required fields for type, actor identity, timestamp, method, and evidence hash/reference. | `FR-045` |
| `DFR-06-004` | Audit timeline and reports shall explicitly distinguish normal approvals, human-signature approvals, and system attestation outcomes. | `FR-046` |
| `DFR-06-005` | Timeout auto-approve with signature-required step may generate system attestation only when explicitly enabled and must use dedicated non-human signer identity plus reason `timeout_auto_approve`. | `FR-084`, `FR-085` |
| `DFR-06-006` | Steps tagged `legal_human_signature_required` shall always disallow timeout auto-approve, regardless of attestation enablement. | `FR-096` |
| `DFR-06-007` | Evidence and signature artifacts shall be retention-policy configurable and linked to archival/purge policy references. | `NFR-006` |

## 5. Domain Objects (Conceptual)
1. `workflow.signature_policy`
- Step-level signature rules and legal flags.
2. `workflow.signature_evidence`
- Immutable evidence record for human signature or system attestation.
3. `workflow.attestation_policy`
- Admin-controlled enablement for timeout-generated system attestations.
4. `workflow.evidence_audit_projection`
- Reporting-friendly normalized event projection.

## 6. Signature and Attestation Policy Contract
### 6.1 Policy Flags
1. `sign_required` (`true/false`)
2. `legal_human_signature_required` (`true/false`)
3. `allow_system_attestation_on_timeout` (`true/false`)

### 6.2 Timeout Policy Compatibility Matrix
| Condition | `auto-approve` | `auto-reject` | `escalate-only` |
|---|---|---|---|
| `sign_required=false` | Allowed | Allowed | Allowed |
| `sign_required=true` and `allow_system_attestation_on_timeout=true` and not legal-human step | Allowed with `system_attestation` | Allowed (no evidence artifact created) | Allowed (escalation target may still require signature) |
| `sign_required=true` and `allow_system_attestation_on_timeout=false` | Not allowed | Allowed | Allowed |
| `legal_human_signature_required=true` | Not allowed | Allowed | Allowed |

### 6.3 Deterministic Timeout Ordering
1. Timeout handler evaluates legal-human restriction first.
2. Then attestation enablement is checked.
3. If any rule denies auto-approve, fallback timeout action from matrix is applied.

## 7. Evidence Model and Immutability Contract
### 7.1 Evidence Type Taxonomy
1. `human_signature`
2. `system_attestation`

### 7.2 Mandatory Immutable Fields
1. `evidence_type`
2. `signer_actor_id` (human or dedicated service identity)
3. `occurred_at_utc`
4. `capture_method` — valid values: `click_to_sign`, `drawn_signature`, `otp_challenge`, `system_auto_attest`
5. `reason_code`
6. `evidence_hash`
7. `evidence_ref`
8. `instance_id`
9. `task_id`

### 7.3 Immutability Rules
1. Evidence fields are write-once after creation.
2. Updates are disallowed; corrections require superseding evidence with linkage and reason.
3. Evidence hash mismatch is an integrity incident and blocks signed completion.

## 8. Audit and Reporting Contract
### 8.1 Required Distinctions
Reports shall separate:
1. `standard_approval`
2. `human_signature_approval`
3. `system_attestation_approval`
4. `signature_required_blocked`

### 8.2 Labeling Rules
1. `system_attestation` must never be displayed as human signature.
2. Any UI/report label must reflect true evidence type.

### 8.3 Queryability
1. Evidence queries support filtering by type, actor, reason code, and time range.
2. Compliance audit export must include cryptographic reference fields.

## 9. Retention and Lifecycle Hooks (`NFR-006`)
1. Evidence retention policy is configurable by policy profile.
2. Evidence lifecycle events reference `SRS-09` archival/purge controls.
3. Purge eligibility checks must preserve legal-hold constraints.

## 10. APIs and Events (Evidence Domain)
### 10.1 Logical Operations
1. `validate_signature_policy(step_id)`
2. `record_human_signature(task_id, actor, payload)`
3. `record_system_attestation(task_id, service_actor, reason_code, payload)`
4. `verify_evidence_integrity(evidence_id)`
5. `query_evidence(filters)`
6. `export_evidence_audit_report(filters)`

### 10.2 Required Audit Events
1. `workflow.signature.policy_validated`
2. `workflow.signature.evidence_recorded`
3. `workflow.signature.integrity_verified`
4. `workflow.signature.integrity_failed`
5. `workflow.signature.timeout_attestation_created`
6. `workflow.signature.legal_constraint_blocked`

## 11. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-FR-043-001` | `FR-043` | Configure step with `sign_required=true` | Policy persisted and enforced |
| `TC-FR-044-001` | `FR-044` | Attempt signed completion without evidence | Completion blocked |
| `TC-FR-044-002` | `FR-044` | Provide valid evidence then complete | Completion allowed |
| `TC-FR-045-001` | `FR-045` | Record evidence artifact | All mandatory immutable fields stored |
| `TC-FR-045-002` | `FR-045` | Attempt update to immutable evidence fields | Update rejected |
| `TC-FR-046-001` | `FR-046` | Generate audit report with mixed outcomes | Report clearly distinguishes outcome categories |
| `TC-FR-084-001` | `FR-084` | Timeout auto-approve with attestation enabled | `system_attestation` artifact created with dedicated identity and reason |
| `TC-FR-085-001` | `FR-085` | Timeout auto-approve requested while attestation disabled | Policy validation rejects auto-approve option |
| `TC-FR-096-001` | `FR-096` | Legal-human step with timeout auto-approve policy | Auto-approve blocked regardless of attestation setting |
| `TC-NFR-006-001` | `NFR-006` | Apply retention profile to evidence records | Evidence retention behavior follows policy profile |
| `TC-FR-084-002` | `FR-084`, `FR-046` | Render system attestation in UI/report | Labeled as `system_attestation` and not human signature |
| `TC-FR-045-003` | `FR-045` | Evidence hash verification fails | Integrity incident created; completion blocked |
| `TC-FR-084-003` | `FR-084` | Timeout and manual approve race concurrently | Single terminal outcome; evidence chain consistent |
| `TC-FR-085-002` | `FR-085` | Attestation identity disabled during timeout window | Auto-approve blocked; fallback timeout action applied |
| `TC-NFR-006-002` | `NFR-006` | Purge attempt on legal-hold evidence | Purge denied with policy hold reason |

## 12. Traceability Matrix
| Canonical ID | Covered Sections | Primary Tests |
|---|---|---|
| `FR-043` | 4, 6 | `TC-FR-043-001` |
| `FR-044` | 4, 7 | `TC-FR-044-001`, `TC-FR-044-002` |
| `FR-045` | 4, 7 | `TC-FR-045-001`, `TC-FR-045-002`, `TC-FR-045-003` |
| `FR-046` | 4, 8 | `TC-FR-046-001`, `TC-FR-084-002` |
| `FR-084` | 4, 6, 7 | `TC-FR-084-001`, `TC-FR-084-002` |
| `FR-085` | 4, 6 | `TC-FR-085-001` |
| `FR-096` | 4, 6 | `TC-FR-096-001` |
| `NFR-006` | 4, 9 | `TC-NFR-006-001` |

## 13. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-06-01` | Timeout and manual approve submitted concurrently | Deterministic ordering preserves single terminal outcome and evidence chain | Tech Lead | `TC-FR-084-003` |
| `EC-06-02` | Dedicated attestation identity disabled mid-process | Timeout auto-approve blocked; escalation/auto-reject fallback applied | Workflow Admin | `TC-FR-085-002` |
| `EC-06-03` | Legal-hold flag on evidence eligible for purge | Purge denied until legal hold cleared | Compliance Lead | `TC-NFR-006-002` |

## 14. Sign-off Checklist
1. All inherited requirements in Section 3 are mapped in Section 12.
2. Timeout policy matrix has deterministic and legally safe behavior.
3. Evidence immutability and integrity failure handling are explicit.
4. Reports cannot mislabel system attestation as human signature.
5. Retention hooks align with `SRS-09` archival/purge framework.

## 15. Open Issues
1. Cryptographic signature format/profile (algorithm suite) requires security baseline alignment with platform standards.
2. Legal hold governance workflow ownership needs formal RACI sign-off.

## 16. Next Document
After approval of `SRS-06`, proceed to `srs_07_access_security_governance.md`.
