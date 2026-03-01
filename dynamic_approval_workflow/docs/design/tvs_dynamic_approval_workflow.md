# Test & Validation Specification (TVS) — Dynamic Approval Workflow

Version: `v0.1-draft`  
Date: `2026-03-01`  
Owner: `QA Lead`  
Status: `draft`

---

## 1. Purpose

Define the authoritative validation strategy for the `dynamic_approval_workflow` module, including:

1. What must be tested.
2. How tests are executed.
3. What evidence is required for release.
4. How requirements are proven through traceable test outcomes.

This document is the validation contract used with:

1. `SDS` (`docs/design/sds_dynamic_approval_workflow.md`)
2. `OMB` (`docs/design/omb_dynamic_approval_workflow.md`)
3. `ITM` (`docs/design/itm_dynamic_approval_workflow.md`)
4. `RTM` (`docs/design/rtm_dynamic_approval_workflow.md`)

## 2. Scope

### 2.1 In Scope

1. Functional behavior from SRS-01..SRS-10.
2. Non-functional validation for reliability, security, retention, and traceability.
3. Odoo backend tests, integration tests, and selected UI behavior validation.
4. Multi-company isolation and access-control verification.
5. Release evidence collection and sign-off criteria.

### 2.2 Out of Scope

1. Third-party infrastructure SLA verification outside module control.
2. Full browser compatibility matrix beyond agreed project targets.
3. Penetration testing executed by external security vendors.

## 3. Source References

1. `docs/srs/baseline/dynamic_approval_workflow_srs_v1.3.md`
2. `docs/srs/baseline/srs_00_master_traceability.md`
3. `docs/srs/detailed/srs_01_*` through `docs/srs/detailed/srs_10_*`
4. `docs/srs/supplementary/srs_to_development_bridge_plan.md`
5. Odoo 19 backend testing reference: `https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html`

## 4. Validation Objectives

Release quality is accepted only when all objectives are met:

1. All in-scope `FR-*` and `NFR-*` have mapped test coverage in RTM.
2. No unresolved severity `Critical` or `High` defects remain open.
3. Required automated suites pass in CI for release candidate branch.
4. Traceability chain is complete from requirement to evidence artifact.
5. Security, audit, and evidence policies satisfy compliance requirements.

## 5. Test Strategy

### 5.1 Test Levels

| Level | Purpose | Primary Technique | Owner |
|---|---|---|---|
| Unit | Validate model methods, constraints, utility functions | Odoo `TransactionCase` and targeted model assertions | Engineering |
| Integration | Validate cross-model workflow execution and side effects | Scenario tests with setup fixtures and action invocations | Engineering + QA |
| System | Validate end-to-end workflow lifecycle and user outcomes | Business-flow test scripts and smoke suite | QA |
| Regression | Prevent breakage in previously validated behavior | Curated baseline suite by risk tier | QA |
| Non-functional | Validate performance, reliability, retention, and security controls | Load probes, retention runs, and policy assertions | QA + Ops + Security |

### 5.2 Domain Coverage Strategy

| SRS Domain | Minimum Coverage Requirement |
|---|---|
| SRS-01 Definition/versioning | Publish lifecycle, version immutability, conflict handling |
| SRS-02 Binding/enforcement | Gate checks, callback behavior, interception failure paths |
| SRS-03 BPMN modeling/viewer | Model validation, diagram rendering, schema sanity checks |
| SRS-04 Runtime orchestration | Routing, parallel/quorum joins, timeout decisions, incidents |
| SRS-05 Human tasks | Assignment, delegation, reminders, resolution rules |
| SRS-06 Signature/evidence | Signature capture policy, evidence integrity, legal-hold behavior |
| SRS-07 Access/security | Role boundaries, record rules, multi-company isolation |
| SRS-08 Notifications/webhooks | Delivery flow, retry policy, webhook signature and schema |
| SRS-09 Operations/reliability | Dashboard metrics, archival/purge, backup/restore assertions |
| SRS-10 Data/API/traceability | Idempotency, contracts, test traceability completeness |

### 5.3 Test Design Rules

1. Each test case validates one primary behavior and may include bounded edge assertions.
2. Each critical requirement has positive, negative, and boundary coverage.
3. Compliance-critical requirements include explicit audit-log assertions.
4. Tests must be deterministic and isolated from non-required external systems.

## 6. Environment and Data Strategy

### 6.1 Environment Matrix

| Environment | Purpose | Data Policy | Required for Sign-off |
|---|---|---|---|
| Local Dev | Fast iteration during implementation | Synthetic developer fixtures | No |
| CI | Mandatory automated gate | Seeded deterministic fixtures | Yes |
| Staging | Pre-release validation and smoke/UAT support | Production-like anonymized dataset | Yes |

### 6.2 Data Rules

1. Use deterministic fixture datasets for automated tests.
2. Cover at least two companies for isolation tests.
3. Include records triggering delegation, timeout, incident, and retention paths.
4. Do not use live personal data in test evidence.

## 7. Automation and Execution

### 7.1 Mandatory Command Stack

Run in this order for each merge candidate:

1. `python -m py_compile <changed_python_files>`
2. `odoo-bin -d <db> -i dynamic_approval_workflow --stop-after-init`
3. `odoo-bin -d <db> --test-tags /dynamic_approval_workflow`
4. `ruff check dynamic_approval_workflow`
5. `eslint dynamic_approval_workflow/static/src`
6. `pre-commit run --all-files` (if configured)

### 7.2 Automation Policy

| Test Type | Automation Requirement |
|---|---|
| Unit tests | Mandatory automated |
| Integration tests | Mandatory automated for critical flows |
| Regression smoke | Mandatory automated |
| UAT scenarios | Manual, with documented evidence |
| Exploratory tests | Manual, risk-driven |

## 8. Defect Management Policy

### 8.1 Severity Definitions

| Severity | Definition | Release Impact |
|---|---|---|
| Critical | Data corruption, security break, or workflow bypass | Blocks release |
| High | Major business flow failure with no acceptable workaround | Blocks release |
| Medium | Significant issue with controlled workaround | Allowed only with approved waiver |
| Low | Minor defect with limited business impact | Does not block release |

### 8.2 Triage Rules

1. Each failed critical-path test creates a tracked defect.
2. Waivers require owner, rationale, mitigation, and expiration date.
3. Reopened defects must retain historical evidence links.

## 9. Entry and Exit Criteria

### 9.1 Entry Criteria (Test Execution Start)

1. Relevant `TASK-*` implementations merged to test branch.
2. Required test data and environments are available.
3. RTM rows exist for in-scope requirements.

### 9.2 Exit Criteria (Release Recommendation)

1. RTM status for release scope is `Pass` or approved `Waived`.
2. No open `Critical` or `High` defects.
3. Mandatory automated suites pass on latest release candidate.
4. Evidence index is complete and reviewed.

## 10. Evidence and Reporting

### 10.1 Required Evidence Types

1. Automated test logs (CI links or archived logs).
2. Manual execution records for UAT and exploratory scenarios.
3. Defect reports and waiver approvals.
4. Final summary report per release candidate.

### 10.2 Evidence Storage

Primary index file:

1. `docs/design/test_evidence_index.md`

Recommended artifact directory structure:

1. `docs/design/evidence/<release_tag>/automated/`
2. `docs/design/evidence/<release_tag>/manual/`
3. `docs/design/evidence/<release_tag>/defects/`

## 11. RTM Integration Rules

1. Every in-scope `FR-*` and `NFR-*` must map to one or more `TC-*`.
2. Every `TC-*` must link to a concrete execution evidence record.
3. Every failed `TC-*` must link to a defect ID or approved waiver.
4. RTM status changes must include timestamp and owner.

## 12. Test Case ID Convention

Use stable identifiers:

1. `TC-FR-<id>-NNN` for functional requirements.
2. `TC-NFR-<id>-NNN` for non-functional requirements.
3. `TC-INT-<domain>-NNN` for cross-domain integration scenarios.
4. `TC-REG-<scope>-NNN` for regression suite cases.

## 13. Risks and Assumptions

1. Assumes completion of remaining SRS blockers before final release sign-off.
2. Assumes CI environment can run Odoo module tests consistently.
3. Assumes OMB and ITM remain authoritative and version-controlled.

## 14. Sign-off

| Role | Name | Date | Approval |
|---|---|---|---|
| QA Lead | | | |
| Tech Lead | | | |
| Security Lead | | | |
| Product Owner | | | |
