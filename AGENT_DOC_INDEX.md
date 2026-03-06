# Agent Documentation Index

Index ID: `ADI-00`
Version: `v1.0`
Status: `active`
Owner: `Tech Lead`
Last Verified: `2026-03-06`

---

## 1. Purpose

Single lightweight entrypoint for code agents.

Read this file first, then load only task-relevant documents from the routing tables below.

## 2. Bootstrap Rules

1. Always read:
   - `AGENTS.md`
   - `LESSONS.md`
2. Do not load full SRS or full OMB portfolios by default.
3. Prefer indexed entrypoints (domain `README.md` files and `dynamic_approval_workflow/docs/design/omb/OMB-00-index.md`) before opening detailed documents.

## 3. Authority Registry

| Domain | Canonical Document | Notes |
|---|---|---|
| Agent coding policy | `AGENTS.md` | Primary implementation rules |
| Project runtime constraints | `CLAUDE.md` | Repo-specific guardrails |
| Requirement baseline | `dynamic_approval_workflow/docs/srs/baseline/dynamic_approval_workflow_srs_v1.3.md` | FR/NFR source of truth |
| Architecture decisions | `dynamic_approval_workflow/docs/design/sds_dynamic_approval_workflow.md` + ADR index | SDS + accepted ADRs |
| Field/model/view/security contracts | `dynamic_approval_workflow/docs/design/omb/OMB-00-index.md` | OMB split index (`OMB-01..07`) |
| Task/dependency order | `dynamic_approval_workflow/docs/design/itm_dynamic_approval_workflow.md` | Task manifest |
| Validation strategy | `dynamic_approval_workflow/docs/design/tvs_dynamic_approval_workflow.md` | Testing contract |
| Requirement-test traceability | `dynamic_approval_workflow/docs/design/rtm_dynamic_approval_workflow.md` | Test coverage mapping |
| Evidence tracking | `dynamic_approval_workflow/docs/design/test_evidence_index.md` | Release evidence register |
| Operational implementation plans | `docs/plans/README.md` | Historical and execution plans |

## 4. Task Router (deterministic load order)

### 4.1 Implementation / feature task

1. `AGENTS.md`
2. `LESSONS.md`
3. `dynamic_approval_workflow/docs/design/itm_dynamic_approval_workflow.md`
4. `dynamic_approval_workflow/docs/design/omb/OMB-00-index.md` and relevant OMB part
5. `dynamic_approval_workflow/docs/design/sds_dynamic_approval_workflow.md`
6. `dynamic_approval_workflow/docs/design/adr/README.md` and relevant ADR
7. Targeted child SRS document only if behavior intent is unclear

### 4.2 Bugfix task

1. `AGENTS.md`
2. `LESSONS.md`
3. Relevant OMB section first
4. SDS + relevant ADR
5. Targeted SRS child document only if needed

### 4.3 Testing task

1. `dynamic_approval_workflow/docs/design/tvs_dynamic_approval_workflow.md`
2. `dynamic_approval_workflow/docs/design/rtm_dynamic_approval_workflow.md`
3. `dynamic_approval_workflow/docs/design/test_evidence_index.md`
4. OMB/ITM sections for impacted scope

### 4.4 Security task

1. `AGENTS.md`
2. `LESSONS.md`
3. `dynamic_approval_workflow/docs/design/omb/OMB-03-core-security.md`
4. SDS security/enforcement sections + relevant ADRs
5. `dynamic_approval_workflow/docs/srs/detailed/srs_07_access_security_governance.md`

### 4.5 Documentation task

1. Related index first (`dynamic_approval_workflow/docs/srs/README.md`, `dynamic_approval_workflow/docs/design/adr/README.md`, `dynamic_approval_workflow/docs/design/omb/OMB-00-index.md`, `docs/plans/README.md`)
2. Target document
3. Update indexes if file paths or canonical references changed

## 5. Secondary Indexes

- SRS index: `dynamic_approval_workflow/docs/srs/README.md`
- Design ADR index: `dynamic_approval_workflow/docs/design/adr/README.md`
- OMB index: `dynamic_approval_workflow/docs/design/omb/OMB-00-index.md`
- Plans index: `docs/plans/README.md`

## 6. Non-default / legacy references

These are not default load targets:

- `dynamic_approval_workflow/docs/design/sds_dynamic_approval_workflow_v0.2_backup.md`
- `dynamic_approval_workflow/docs/srs/baseline/dynamic_approval_workflow_srs_v1.1.md`
- `docs/workflow_srs.md`
