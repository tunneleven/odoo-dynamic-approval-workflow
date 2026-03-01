# Test Evidence Index — Dynamic Approval Workflow

Version: `v0.1-draft`  
Date: `2026-03-01`  
Owner: `QA Lead`  
Status: `active-template`

---

## 1. Purpose

Provide a single index for all validation evidence referenced by:

1. `TVS` (`docs/design/tvs_dynamic_approval_workflow.md`)
2. `RTM` (`docs/design/rtm_dynamic_approval_workflow.md`)
3. Release sign-off records

No requirement is considered validated without an evidence record in this index.

## 2. Evidence ID Convention

Use stable IDs:

1. `E-AUTO-YYYYMMDD-NNN` for automated test evidence.
2. `E-MAN-YYYYMMDD-NNN` for manual test evidence.
3. `E-DEF-YYYYMMDD-NNN` for defect/waiver evidence.
4. `E-REL-YYYYMMDD-NNN` for release summary evidence.

## 3. Required Metadata

Each evidence entry must include:

1. Evidence ID
2. Date
3. Release candidate tag or branch
4. Requirement and test case linkage
5. Execution owner
6. Storage location
7. Result summary

## 4. Evidence Register

| Evidence ID | Date | Release/Branch | Type | Requirement IDs | Test Case IDs | Owner | Location | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|
| E-AUTO-20260301-001 | 2026-03-01 | `rc/TBD` | Automated | FR-001, FR-007 | TC-FR-001-001, TC-FR-007-001 | QA Lead | `TBD` | Not Run | Initial placeholder |
| E-AUTO-20260301-002 | 2026-03-01 | `rc/TBD` | Automated | FR-079 | TC-FR-079-001 | QA Lead | `TBD` | Not Run | Multi-company isolation suite |
| E-MAN-20260301-001 | 2026-03-01 | `rc/TBD` | Manual | FR-013 | TC-FR-013-001 | QA Engineer | `TBD` | Not Run | BPMN UI validation session |
| E-DEF-20260301-001 | 2026-03-01 | `rc/TBD` | Defect/Waiver | FR-043, FR-096 | TC-FR-043-001, TC-FR-096-001 | Security Lead | `TBD` | Open | Blocker linkage for crypto policy |

## 5. Release Evidence Checklist

Complete this checklist per release candidate:

1. All mandatory automated suites have archived logs.
2. All manual/UAT scenarios have signed execution records.
3. All failed tests are linked to defects or approved waivers.
4. RTM has no unresolved `Critical`/`High` blocker without formal approval.
5. Final release summary evidence is recorded.

## 6. Evidence Storage Layout

Recommended paths:

1. `docs/design/evidence/<release_tag>/automated/`
2. `docs/design/evidence/<release_tag>/manual/`
3. `docs/design/evidence/<release_tag>/defects/`
4. `docs/design/evidence/<release_tag>/release-summary/`

Index should store either:

1. Relative repo paths for checked-in artifacts.
2. Stable CI URLs for generated pipeline logs.

## 7. Governance Rules

1. Evidence entries are append-only; corrections must preserve history.
2. Deleted or inaccessible evidence links invalidate related RTM `Pass` status.
3. Owner must update index within one business day after execution.
4. QA Lead reviews index completeness before release sign-off.

## 8. Sign-off

| Role | Name | Date | Approval |
|---|---|---|---|
| QA Lead | | | |
| Tech Lead | | | |
| Product Owner | | | |
