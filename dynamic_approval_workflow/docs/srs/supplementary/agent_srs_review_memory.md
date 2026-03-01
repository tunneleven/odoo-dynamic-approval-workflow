# Agent SRS Review Memory

Version: `v1.1`
Date: `2026-03-01`
Purpose: Capture iterative review lessons so each next SRS improves deterministically.

## Iteration 1
### SRS ID
`SRS-03`

### Top Mistake/GAP Patterns
1. Edge-case scenarios documented but not fully promoted into acceptance criteria.
2. Performance target defined without fixed benchmark profile dataset.
3. Schema evolution assumption left implicit.

### Root Cause
1. Drafting focused on functional completeness before QA execution detail.
2. Ops benchmark detail deferred too late.
3. Cross-SRS contract dependency (`SRS-10`) not explicitly pinned in acceptance criteria.

### Correction Used
1. Added explicit gap callout in review and action plan.
2. Captured performance benchmark as open issue with closure action.
3. Added forward action to include schema compatibility matrix.

### Rule for Next SRS
1. Promote most edge cases directly into acceptance tests where feasible.
2. For every NFR, define concrete measurement dataset/conditions.
3. If relying on another SRS contract, state dependency explicitly in checklist.

### Carry-forward Checklist Items
1. Check no "planned-only" critical edge tests remain.
2. Confirm benchmark/test profile is measurable.
3. Verify cross-SRS dependency references are explicit.

## Iteration 2
### SRS ID
`SRS-05`

### Top Mistake/GAP Patterns
1. Some important edge cases left as planned tests instead of full acceptance tests.
2. Concurrency race ordering (delegation vs escalation) not explicitly codified.
3. Mobile compatibility baseline too narrow for enterprise device diversity.

### Root Cause
1. Complexity of human-task scenarios pushed less-common cases to backlog.
2. Timestamp race conditions not fully modeled in first draft.
3. NFR validation treated as minimal threshold rather than broad compatibility matrix.

### Correction Used
1. Added explicit gap register and action items.
2. Flagged deterministic ordering requirement for implementation design follow-up.
3. Marked need for expanded mobile QA matrix.

### Rule for Next SRS
1. Include deterministic ordering for race-sensitive flows in main body.
2. Keep only low-impact planned tests; critical/important edge paths must be in acceptance table.
3. For compliance/security domains, define coverage matrix breadth upfront.

### Carry-forward Checklist Items
1. Race condition ordering explicitly documented.
2. Critical edge tests not deferred.
3. Validation breadth (profiles/modes/channels) explicit in acceptance scenarios.

## Iteration 3
### SRS ID
`SRS-06`

### Top Mistake/GAP Patterns
1. A critical race condition (timeout vs manual action) remained planned-only.
2. Crypto algorithm profile left as open issue without immediate cross-link closure.
3. Legal hold operations lacked explicit ownership workflow.

### Root Cause
1. Compliance-heavy drafting prioritized policy matrix over execution races.
2. Security detail deferred to adjacent SRS without explicit closure criteria.
3. Operations responsibilities assumed rather than codified.

### Correction Used
1. Recorded the race as important review action and carry-forward blocker.
2. Added explicit dependency to security domain alignment.
3. Flagged legal-hold RACI integration requirement.

### Rule for Next SRS
1. Security/compliance critical races must be direct acceptance tests.
2. Any deferred dependency must include destination SRS and closure condition.
3. Governance responsibilities should include owner role and process entry/exit.

### Carry-forward Checklist Items
1. No planned-only test for compliance-critical race paths.
2. Deferred security dependencies carry explicit closure criteria.
3. Ownership/RACI visible for governance controls.

## Iteration 4
### SRS ID
`SRS-07`

### Top Mistake/GAP Patterns
1. Remaining concurrency edge tests still deferred as planned-only.
2. Architecture-sensitive details (cache invalidation strategy) remained in open issues.
3. Exception governance path defined functionally but not fully operationalized.

### Root Cause
1. Security complexity encouraged conservative deferral of difficult scenarios.
2. Deployment-specific constraints not available in pure SRS drafting context.
3. Governance model drafted at policy layer without runbook-level detail.

### Correction Used
1. Documented exact missing tests and promoted as high-priority action.
2. Flagged need for architecture decision record.
3. Added explicit governance closure action.

### Rule for Next SRS
1. External-contract and reliability docs must include concrete operational behaviors, not only policy statements.
2. Keep open issues minimal and link each to explicit closure artifact.
3. Push high-risk edge cases into acceptance tests whenever deterministic behavior is already defined.

### Carry-forward Checklist Items
1. Minimize planned-only tests for high-risk paths.
2. Bind topology/ops-sensitive statements to explicit artifacts.
3. Ensure operational governance closure criteria are explicit.

## Iteration 5
### SRS ID
`SRS-08`

### Top Mistake/GAP Patterns
1. High-risk operational edge tests remained planned-only.
2. Retry classification policy left as open issue instead of fixed table.
3. Clock-skew tolerance missing exact numeric value.

### Root Cause
1. External contract drafted comprehensively but ops execution detail deferred.
2. Integration and ops policy ownership split created unresolved boundaries.
3. Quantitative thresholds not finalized during document drafting.

### Correction Used
1. Captured promotion requirement for planned edge tests.
2. Added explicit action to publish retry matrix.
3. Added requirement to pin clock skew threshold in ops baseline.

### Rule for Next SRS
1. Ops/reliability SRS must include numeric thresholds where applicable.
2. High-impact failure paths should be acceptance tests, not deferred edges.
3. Ownership split between integration and ops requires explicit closure artifacts.

### Carry-forward Checklist Items
1. Numeric thresholds explicit for reliability/ops items.
2. High-risk ops cases are directly testable in acceptance section.
3. Open issues tied to concrete artifact and owner.

## Iteration 6
### SRS ID
`SRS-09`

### Top Mistake/GAP Patterns
1. Some operational edge cases still deferred as planned-only tests.
2. Alerting formulas were left as open issue rather than embedded baseline.
3. Localization fallback for custom templates unresolved.

### Root Cause
1. Ops complexity and ownership split between product/ops delayed test promotion.
2. Monitoring strategy expected separate runbook artifact not yet authored.
3. Cross-cutting localization policy spans product and ops governance.

### Correction Used
1. Logged high-priority action to convert planned tests.
2. Added explicit requirement to publish alerting appendix.
3. Added policy closure requirement for localization fallback.

### Rule for Next SRS
1. Cross-cutting contract SRS should include explicit handoff artifacts for open issues.
2. Planned-only tests should be limited to non-critical scenarios.
3. Operational formulas should be referenced by name and owner artifact.

### Carry-forward Checklist Items
1. Open issues tie directly to closure artifacts/owners.
2. Critical reliability tests present in acceptance criteria.
3. Cross-domain policies have explicit decision owner.

## Iteration 7
### SRS ID
`SRS-10`

### Top Mistake/GAP Patterns
1. Durability edge tests for idempotency still deferred.
2. Policy parameter (idempotency retention duration) unresolved.
3. Traceability schema lifecycle ownership not finalized.

### Root Cause
1. Cross-cutting platform contracts rely on multiple domain owners.
2. Quantitative retention decisions require operations/legal alignment.
3. Tooling governance for schema evolution was outside initial drafting pass.

### Correction Used
1. Documented high-priority test promotion actions.
2. Tied open policy to explicit SRS-09 dependency.
3. Added governance closure requirement for schema lifecycle.

### Rule for Next Step (Portfolio Review)
1. Validate unresolved open issues across SRSs are non-critical and owned.
2. Confirm cross-SRS dependencies have explicit closure artifacts.
3. Ensure no contradiction in shared terms and contract semantics.

### Carry-forward Checklist Items
1. Open issue owner and closure artifact for each unresolved item.
2. Shared contract terms normalized across SRS files.
3. Cross-SRS traceability consistency pass complete.

## Iteration 8
### SRS ID
`Full Portfolio (SRS-00..SRS-10)` — Consolidated Review

### Top Mistake/GAP Patterns
1. Planned-only edge tests remain at 100% in 8 of 10 child SRS documents.
2. Quantitative thresholds deferred across multiple domains (TTL, retention, clock skew, node count).
3. No centralized glossary causes term normalization issues ("effectively-once" vs "exactly-once").
4. Open issues universally lack deadlines and closure artifact references.
5. DFR-10-004 covers 6 FRs without decomposition.
6. SRS-00 §6.3 incorrectly assigns NFR-015 to SRS-05 (only SRS-09 owns it).

### Root Cause
1. Edge case identification outpaced test authoring cadence.
2. Ops/security/compliance parameters require cross-team alignment not available during SRS drafting.
3. Portfolio grew organically without glossary governance from SRS-00.
4. Open issue template in SRS documents lacks mandatory deadline field.
5. Cross-cutting contract SRS (SRS-10) treated as thin governance overlay.
6. Index maintenance not automated; manual copy errors in traceability matrix.

### Correction Used
1. Created consolidated review report with per-SRS gap register and action plan.
2. Identified 11 Priority 1 actions for baseline freeze readiness.
3. Documented 24 open issues with blocking status classification.
4. Flagged 12 requirement smells across portfolio.
5. Verified 100% canonical FR/NFR coverage across child SRS documents.

### Rule for Next Phase
1. Edge case register must include "promoted" vs "planned" status with mandatory promotion deadline.
2. Quantitative thresholds in NFRs must have at least an interim default value.
3. SRS-00 must include or reference a portfolio glossary as mandatory governance artifact.
4. Open issue template must require: owner, closure artifact, deadline, blocking status.
5. Cross-cutting SRS documents should decompose requirements per-FR, not bundle.

### Carry-forward Checklist Items
1. No child SRS should have >50% planned-only edge cases at baseline freeze.
2. Every NFR must have a measurable threshold (interim values acceptable with calibration flag).
3. Portfolio glossary exists and is referenced from SRS-00.
4. Open issues have owner + artifact + deadline.
5. DFRs map to at most 2 canonical IDs each (decompose if broader).

## Iteration 9
### SRS ID
`Full Portfolio (SRS-00..SRS-10)` — Remediation Pass

### Actions Completed
1. **SRS-00 v1.1**: Removed SRS-05 from NFR-015 assignment; added glossary reference.
2. **SRS-03 v1.2**: Defined "standard-size" (≤75 nodes), converted should→shall, enumerated keyboard ops, specified validation error schema fields, promoted all 4 edge case tests.
3. **SRS-05 v1.2**: Elaborated group expansion (depth-order, de-dup), enumerated 4 fallback source types, defined policy calendar (24/7 UTC default), clarified downgrade/retained/removed semantics, added disabled-user exclusion event, promoted all 4 edge case tests, added 4 new test scenarios.
4. **SRS-06 v1.2**: Completed timeout compatibility matrix (filled auto-reject/escalate-only cells), enumerated `capture_method` values, promoted all 3 edge case tests, added 3 new test scenarios.
5. **SRS-07 v1.2**: Specified grant TTL range (5 min–72 hours, default 24 hours), promoted all 3 edge case tests, added 3 new test scenarios.
6. **SRS-08 v1.2**: Published retry classification matrix (7 response categories), defined clock tolerance (30s), defined replay window default (300s), defined secret rotation overlap (1–24 hours), resolved both open issues, promoted all 3 edge case tests, added 3 new test scenarios.
7. **SRS-09 v1.2**: Defined retention profile durations (short_term 90d, standard 365d, compliance_extended 7y), promoted all 3 edge case tests, added 3 new test scenarios.
8. **SRS-10 v1.2**: Decomposed DFR-10-004 into DFR-10-004a..d (per-FR), split TC-X-10-001 into TC-X-10-001a..d, promoted all 3 edge case tests, added 4 new test scenarios.
9. **Portfolio glossary**: Created `supplementary/portfolio_glossary.md` with 30+ normative term definitions; normalized "effectively-once" as canonical term.
10. **Open issues**: Assigned deadlines to all 21 remaining issues; marked 3 as resolved; identified 2 blocking.
11. **Consolidated report**: Updated all metrics, exit criteria (8/10 pass), maturity rankings, checklist results, contradiction register.

### Post-Remediation Metrics
| Metric | Before | After |
|---|---|---|
| Planned-only edge cases | 26 (39%) | 3 (4%) |
| Requirement smells | 12 | 0 |
| Important gaps | 14 | 0 |
| Open issues without deadlines | 24 | 0 |
| Portfolio contradictions | 3 soft | 1 soft (deadline assigned) |
| Exit criteria passing | 4/10 | 8/10 |
| Blocking open issues | 4 | 2 |

### Remaining Items Requiring Human Action
1. SRS-06 #15: Cryptographic algorithm suite — blocking, requires Security Lead.
2. SRS-10 #23: Idempotency retention duration — blocking, requires Tech Lead + Ops.
3. Stakeholder sign-offs for baseline freeze.
4. Baseline version number assignment.

### Lessons Learned
1. Remediation of all 11 Priority 1 items in a single pass is feasible and efficient.
2. Promoting edge cases creates a cascade of new test IDs that must be added to both acceptance criteria tables AND traceability matrices.
3. Portfolio glossary should be created at SRS-00 time, not retroactively.
4. Open issue deadlines should use phase-relative references (not calendar dates) for resilience to schedule changes.
