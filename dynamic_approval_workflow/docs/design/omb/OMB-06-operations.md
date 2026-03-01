# OMB-06 — `dynamic_approval_operations` Module Specification

Parent: `OMB-00-index.md`
Module: `dynamic_approval_operations`
SDS Reference: `SDS §14`
DFR: `DFR-09-001` through `DFR-09-010`

---

## 1. `__manifest__.py`

```python
{
    'name': 'Dynamic Approval Operations',
    'version': '19.0.1.0.0',
    'category': 'Workflow',
    'summary': 'Operations dashboard, retention, and archival for Dynamic Approval Workflow',
    'description': 'Archival, purge, retention policies, and operations tooling.',
    'author': 'Your Company',
    'website': 'https://github.com/your-org/dynamic-approval-workflow',
    'license': 'LGPL-3',
    'depends': ['dynamic_approval_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/workflow_operations_dashboard.xml',
        'views/workflow_retention_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
```

---

## 2. Models

### 2.1 `workflow.retention.policy`

**File**: `models/workflow_retention_policy.py`
**Description**: Retention profile configuration for archive/purge windows.
**DFR**: `DFR-09-005`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Policy Name` | — | — |
| `profile` | `Selection` | Yes | `standard` | — | — | `Profile` | — | `short_term`, `standard`, `compliance_extended` |
| `retention_days` | `Integer` | Yes | `365` | — | — | `Retention Days` | — | `short_term=90`, `standard=365`, `compliance_extended=2555` |
| `applies_to_model` | `Char(128)` | Yes | — | — | — | `Applies To` | `Target model _name` | — |
| `legal_hold_override` | `Boolean` | — | `False` | — | — | `Legal Hold Override` | `Blocks purge regardless of retention` | — |
| `is_active` | `Boolean` | — | `True` | — | — | `Active` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | — |

**Default Retention Profiles**:

| Profile | Retention Days | Use Case |
|---|---|---|
| `short_term` | 90 | Non-critical runtime data, debug logs |
| `standard` | 365 | Completed instance data, task history, notification records |
| `compliance_extended` | 2555 (7 years) | Audit events, signature evidence, compliance-critical records |

---

### 2.2 `workflow.archive.job`

**File**: `models/workflow_archive_job.py`
**Description**: Archive/purge job execution log.
**DFR**: `DFR-09-005`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | — | — | — | Yes | `Job Name` | — | `compute='_compute_name'`, `store=True` |
| `job_type` | `Selection` | Yes | — | — | Yes | `Type` | — | `archive`, `purge` |
| `policy_id` | `Many2one('workflow.retention.policy')` | Yes | — | Yes | Yes | `Policy` | — | — |
| `state` | `Selection` | Yes | `pending` | Yes | — | `State` | — | `pending`, `running`, `completed`, `failed` |
| `started_at_utc` | `Datetime` | No | — | — | Yes | `Started At` | — | — |
| `completed_at_utc` | `Datetime` | No | — | — | Yes | `Completed At` | — | — |
| `records_processed` | `Integer` | — | `0` | — | — | `Records Processed` | — | — |
| `records_skipped` | `Integer` | — | `0` | — | — | `Records Skipped` | `Legal hold or ineligible` | — |
| `error_message` | `Text` | No | — | — | — | `Error` | — | — |
| `actor_id` | `Many2one('res.users')` | No | — | — | Yes | `Initiated By` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | — |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_run` | — | `self` | `DFR-09-005` |
| `_execute_archive` | — | — | `DFR-09-005` |
| `_execute_purge` | — | — | `DFR-09-005` |
| `_check_eligibility` | `record` | `bool` | `DFR-09-005` |

---

## 3. Wizards

### 3.1 Archive Wizard

**File**: `wizards/workflow_archive_wizard.py`
**Model**: `workflow.archive.wizard` (TransientModel)
**Description**: Launch archive job with policy selection and confirmation.

| Field Name | Type | Required | Default | String |
|---|---|---|---|---|
| `policy_id` | `Many2one('workflow.retention.policy')` | Yes | — | `Retention Policy` |
| `preview_count` | `Integer` | — | — | `Eligible Records` |
| `confirm` | `Boolean` | — | `False` | `I confirm this action` |

**Methods**:

| Method | Logic |
|---|---|
| `action_preview` | Count eligible records based on policy; set `preview_count` |
| `action_archive` | Validate `confirm=True`; create `workflow.archive.job`; run |

**View**: `wizards/workflow_archive_wizard_views.xml`

```
┌──────────────────────────────────────────┐
│ Archive Workflow Data                     │
│                                          │
│ Retention Policy: [policy_id ▼]          │
│                                          │
│ [Preview] → Eligible Records: 142        │
│                                          │
│ ☐ I confirm this action                  │
│                                          │
│ [Archive]  [Cancel]                      │
└──────────────────────────────────────────┘
```

### 3.2 Purge Wizard

**File**: `wizards/workflow_purge_wizard.py`
**Model**: `workflow.purge.wizard` (TransientModel)
**Description**: Launch purge job with policy, confirmation, and mandatory reason.

| Field Name | Type | Required | Default | String |
|---|---|---|---|---|
| `policy_id` | `Many2one('workflow.retention.policy')` | Yes | — | `Retention Policy` |
| `reason` | `Text` | Yes | — | `Purge Reason` |
| `preview_count` | `Integer` | — | — | `Eligible Records` |
| `legal_hold_count` | `Integer` | — | — | `Legal Hold Records (excluded)` |
| `confirm` | `Boolean` | — | `False` | `I confirm permanent deletion` |

**Methods**:

| Method | Logic |
|---|---|
| `action_preview` | Count eligible + legal hold records |
| `action_purge` | Validate `confirm=True` + `reason`; create `workflow.archive.job` (type=purge); run; emit audit event |

**Purge Confirmation UX:**

The purge wizard uses a two-step confirmation to prevent accidental data loss:
1. User clicks "Preview" → `action_preview` populates `preview_count` and `legal_hold_count`.
2. User must check the `confirm` checkbox AND enter a mandatory `reason` text.
3. The "Purge" button is only enabled when both `confirm=True` and `reason` is not empty.
4. On confirmation, an audit event `ops.purge.executed` is emitted with the purge reason and record count.

---

## 4. Cron Jobs

**File**: `data/ir_cron_data.xml`

| XML ID | Name | Model | Method | Interval | Active | DFR |
|---|---|---|---|---|---|---|
| `ir_cron_archive_eligible` | `Workflow: Archive Eligible Records` | `workflow.archive.job` | `_cron_run_archive` | 1 day | Yes | `DFR-09-005` |

### 4.1 Cron Method Signature

| Model | Method | Description |
|---|---|---|
| `workflow.archive.job` | `_cron_run_archive()` | Find active archive policies; check eligibility; set `active=False` on eligible records |

---

## 5. Views

### 5.1 Operations Dashboard

**File**: `views/workflow_operations_dashboard.xml`

The dashboard is implemented as a Kanban view with aggregate stat cards. It provides drill-down to instance, task, and incident list views.

**XML ID**: `view_workflow_operations_dashboard`
**Model**: `workflow.instance` (aggregated)
**View Mode**: `kanban` (custom template)

**Dashboard Metrics** (DFR-09-001):

| Card | Domain / Computation | Action |
|---|---|---|
| Active Workflows | `state in (running, waiting_human, waiting_timer)` | → Instance list (running filter) |
| Overdue Tasks | `workflow.task: is_overdue=True, status in (pending, assigned)` | → Task list (overdue filter) |
| Open Incidents | `workflow.incident: state in (open, triaged)` | → Incident list (open filter) |
| Completed Today | `state in (completed_approved, completed_rejected), ended_at_utc >= today` | → Instance list (completed filter) |

**Drill-Down Filters**: Company, Definition, Time Range.

### 5.2 Retention Policy Views

**XML ID**: `view_workflow_retention_policy_form`

```
┌──────────────────────────────────────────┐
│ [sheet]                                  │
│   <group>                                │
│     <group>                              │
│       name                               │
│       profile                            │
│       retention_days                     │
│     </group>                             │
│     <group>                              │
│       applies_to_model                   │
│       legal_hold_override                │
│       is_active                          │
│       company_id                         │
│     </group>                             │
│   </group>                               │
└──────────────────────────────────────────┘
```

**XML ID**: `view_workflow_retention_policy_list`

| Column | Widget |
|---|---|
| `name` | — |
| `profile` | `badge` |
| `retention_days` | — |
| `applies_to_model` | — |
| `is_active` | `boolean_toggle` |

### 5.3 Archive Job Views

**XML ID**: `view_workflow_archive_job_form`

```
┌──────────────────────────────────────────┐
│ [header]                                 │
│   [button] Run (invisible if != pending) │
│   <statusbar field="state" />            │
│                                          │
│ [sheet]                                  │
│   <group>                                │
│     <group>                              │
│       name                               │
│       job_type                           │
│       policy_id                          │
│       actor_id                           │
│     </group>                             │
│     <group>                              │
│       state                              │
│       records_processed                  │
│       records_skipped                    │
│       started_at_utc                     │
│       completed_at_utc                   │
│     </group>                             │
│   </group>                               │
│   <group string="Error" invisible="not error_message">│
│     error_message                        │
│   </group>                               │
└──────────────────────────────────────────┘
```

**XML ID**: `view_workflow_archive_job_list`

| Column | Widget | Decoration |
|---|---|---|
| `name` | — | — |
| `job_type` | `badge` | — |
| `state` | `badge` | `decoration-success="state == 'completed'"`, `decoration-danger="state == 'failed'"` |
| `records_processed` | — | — |
| `started_at_utc` | — | — |

---

## 6. Menu Structure

**File**: `views/menu_views.xml`

```
Approvals (inherited root)
└── Operations (menu_workflow_operations)       [group_workflow_admin]   seq=70
    ├── Dashboard (menu_workflow_ops_dashboard)  [group_workflow_admin]   seq=10
    ├── Retention Policies                      [group_workflow_admin]   seq=20
    ├── Archive Jobs                            [group_workflow_admin]   seq=30
    └── Purge (wizard action)                   [group_workflow_admin]   seq=40
```

---

## 7. Security

### 7.1 Access Rights (`security/ir.model.access.csv`)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_retention_policy_admin,workflow.retention.policy admin,model_workflow_retention_policy,dynamic_approval_core.group_workflow_admin,1,1,1,1
access_retention_policy_auditor,workflow.retention.policy auditor,model_workflow_retention_policy,dynamic_approval_core.group_workflow_auditor,1,0,0,0
access_archive_job_admin,workflow.archive.job admin,model_workflow_archive_job,dynamic_approval_core.group_workflow_admin,1,1,1,0
access_archive_job_auditor,workflow.archive.job auditor,model_workflow_archive_job,dynamic_approval_core.group_workflow_auditor,1,0,0,0
access_archive_wizard_admin,workflow.archive.wizard admin,model_workflow_archive_wizard,dynamic_approval_core.group_workflow_admin,1,1,1,1
access_purge_wizard_admin,workflow.purge.wizard admin,model_workflow_purge_wizard,dynamic_approval_core.group_workflow_admin,1,1,1,1
```

### 7.2 Record Rules

| XML ID | Model | Domain | Global |
|---|---|---|---|
| `rule_retention_policy_company` | `workflow.retention.policy` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes |
| `rule_archive_job_company` | `workflow.archive.job` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes |

---

## 8. File Structure

```
dynamic_approval_operations/
├── __init__.py
├── __manifest__.py
├── readme/
│   ├── DESCRIPTION.rst
│   └── CONTRIBUTORS.rst
├── models/
│   ├── __init__.py
│   ├── workflow_retention_policy.py
│   └── workflow_archive_job.py
├── views/
│   ├── workflow_operations_dashboard.xml
│   ├── workflow_retention_views.xml
│   └── menu_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── workflow_operations_security.xml
├── wizards/
│   ├── __init__.py
│   ├── workflow_archive_wizard.py
│   ├── workflow_archive_wizard_views.xml
│   ├── workflow_purge_wizard.py
│   └── workflow_purge_wizard_views.xml
├── data/
│   └── ir_cron_data.xml
└── tests/
    ├── __init__.py
    ├── test_retention.py
    └── test_archival.py
```

---

## 9. Archive Eligibility Criteria (DFR-09-005, SDS §14.2)

A record is eligible for archival when **all** conditions are met:

1. Instance in terminal state (`completed_approved`, `completed_rejected`, `cancelled`).
2. All child tasks in terminal state (`completed`, `cancelled`).
3. All callbacks resolved (no pending callback incidents).
4. Retention threshold elapsed (`ended_at_utc + retention_days <= now`).
5. No `legal_hold` override active on the retention policy or instance.

Purge jobs additionally require:

6. Record already archived (`active=False`).
7. Purge generates immutable purge report in `workflow.audit.event`.
