# OMB-02 — `dynamic_approval_core` View and Menu Specifications

Parent: `OMB-00-index.md`
Module: `dynamic_approval_core`

> **Custom Widgets (cross-reference):** Views in this document use the widget `bpmn_xml` which is a custom OWL field widget registered by the `dynamic_approval_bpmn` module (see OMB-05 §3.3). If the BPMN module is not installed, the `bpmn_xml` field renders as a plain `Text` field.

---

## 1. Menu Structure

**Root menu**: `menu_workflow_root`

```
Approvals (menu_workflow_root)                  [group_workflow_approver]  seq=50
├── Definitions (menu_workflow_definitions)      [group_workflow_designer]  seq=10
├── Bindings (menu_workflow_bindings)            [group_workflow_designer]  seq=20
├── My Tasks (menu_workflow_my_tasks)            [group_workflow_approver]  seq=30
├── Instances (menu_workflow_instances)          [group_workflow_approver]  seq=40
├── Incidents (menu_workflow_incidents)          [group_workflow_admin]     seq=50
├── Webhooks (menu_workflow_webhooks)            [group_workflow_admin]     seq=60
└── Configuration                                [group_workflow_admin]     seq=90
    ├── Notification Templates                   [group_workflow_admin]     seq=10
    ├── Delegation Rules                         [group_workflow_admin]     seq=20
    └── Webhook Endpoints                        [group_workflow_admin]     seq=30
```

### 1.1 Action Specifications

| XML ID | Name | Model | View Mode | Domain | Context | Groups |
|---|---|---|---|---|---|---|
| `action_workflow_definition` | `Workflow Definitions` | `workflow.definition` | `list,form` | — | — | `group_workflow_designer` |
| `action_workflow_binding` | `Workflow Bindings` | `workflow.binding` | `list,form` | — | — | `group_workflow_designer` |
| `action_workflow_my_tasks` | `My Tasks` | `workflow.task` | `list,form,kanban` | `[('assignee_user_id','=',uid)]` | — | `group_workflow_approver` |
| `action_workflow_instance` | `Workflow Instances` | `workflow.instance` | `list,form` | — | — | `group_workflow_approver` |
| `action_workflow_incident` | `Incidents` | `workflow.incident` | `list,form` | — | — | `group_workflow_admin` |
| `action_workflow_webhook` | `Outbound Events` | `workflow.outbound.event` | `list,form` | — | — | `group_workflow_admin` |
| `action_notification_template` | `Notification Templates` | `workflow.notification.template` | `list,form` | — | — | `group_workflow_admin` |
| `action_delegation_record` | `Delegation Rules` | `workflow.delegation.record` | `list,form` | — | — | `group_workflow_admin` |
| `action_webhook_endpoint` | `Webhook Endpoints` | `workflow.webhook.endpoint` | `list,form` | — | — | `group_workflow_admin` |

---

## 2. `workflow.definition` Views

### 2.1 Form View

**XML ID**: `view_workflow_definition_form`
**Priority**: `10`

```
┌─────────────────────────────────────────────────────┐
│ [header]                                            │
│   <statusbar> (no widget — definition has no state) │
│   [button] Create Draft Version                     │
│                                                     │
│ [sheet]                                             │
│   <div class="oe_title">                            │
│     <h1> name </h1>                                 │
│   </div>                                            │
│                                                     │
│   <group>                                           │
│     <group>                                         │
│       definition_key (readonly after first publish)  │
│       company_id                                    │
│     </group>                                        │
│     <group>                                         │
│       tag_ids (widget="many2many_tags")              │
│       version_count                                 │
│     </group>                                        │
│   </group>                                          │
│                                                     │
│   <notebook>                                        │
│     <page string="Description">                     │
│       description (widget="html")                   │
│     </page>                                         │
│     <page string="Versions">                        │
│       version_ids (list inline)                     │
│         → version, state, effective_from_utc,       │
│           effective_to_utc, published_at_utc        │
│     </page>                                         │
│   </notebook>                                       │
│                                                     │
│ [chatter] mail.thread + mail.activity.mixin         │
└─────────────────────────────────────────────────────┘
```

### 2.2 List View

**XML ID**: `view_workflow_definition_list`
**Priority**: `10`

| Column | Widget | Optional |
|---|---|---|
| `name` | — | No |
| `definition_key` | — | No |
| `company_id` | — | No |
| `version_count` | — | No |
| `tag_ids` | `many2many_tags` | Yes |

### 2.3 Search View

**XML ID**: `view_workflow_definition_search`

| Element | Type | Field/Domain |
|---|---|---|
| `name` | field | — |
| `definition_key` | field | — |
| `company_id` | field | — |
| Archived | filter | `[('active','=',False)]` |
| My Company | filter | `[('company_id','=',user.company_id.id)]` |

---

## 3. `workflow.binding` Views

### 3.1 Form View

**XML ID**: `view_workflow_binding_form`
**Priority**: `10`

```
┌─────────────────────────────────────────────────────┐
│ [header]                                            │
│   [button] Validate       (type="object")           │
│   [button] Enable         (invisible if is_active)  │
│   [button] Disable        (invisible if not active) │
│                                                     │
│ [sheet]                                             │
│   <div class="oe_button_box">                       │
│     [stat_button] Instances                         │
│   </div>                                            │
│   <div class="oe_title">                            │
│     <h1> name </h1>                                 │
│   </div>                                            │
│                                                     │
│   <group string="Binding Target">                   │
│     <group>                                         │
│       definition_id                                 │
│       target_model                                  │
│       target_action_method                          │
│     </group>                                        │
│     <group>                                         │
│       enforcement_mode                              │
│       compliance_critical                           │
│       is_active                                     │
│       binding_priority                              │
│       company_id                                    │
│     </group>                                        │
│   </group>                                          │
│                                                     │
│   <notebook>                                        │
│     <page string="Scopes">                          │
│       scope_ids (list editable="bottom")            │
│         → scope_type, scope_company_id,             │
│           scope_group_id, scope_domain              │
│     </page>                                         │
│     <page string="Callback">                        │
│       <group>                                       │
│         callback_model                              │
│         callback_method                             │
│         callback_execution_principal                │
│         callback_service_user_id                    │
│           (invisible unless principal=service)      │
│         callback_idempotency_policy                 │
│       </group>                                      │
│     </page>                                         │
│     <page string="Warning">                         │
│       ui_warning_message                            │
│     </page>                                         │
│   </notebook>                                       │
│                                                     │
│ [chatter]                                           │
└─────────────────────────────────────────────────────┘
```

### 3.2 List View

**XML ID**: `view_workflow_binding_list`

| Column | Widget | Optional |
|---|---|---|
| `name` | — | No |
| `definition_id` | — | No |
| `target_model` | — | No |
| `target_action_method` | — | No |
| `enforcement_mode` | `badge` | No |
| `is_active` | `boolean_toggle` | No |
| `company_id` | — | No |

### 3.3 Search View

**XML ID**: `view_workflow_binding_search`

| Element | Type | Field/Domain |
|---|---|---|
| `name` | field | — |
| `target_model` | field | — |
| `definition_id` | field | — |
| `enforcement_mode` | field | — |
| Active | filter | `[('is_active','=',True)]` |
| Compliance Critical | filter | `[('compliance_critical','=',True)]` |
| By Enforcement | group_by | `enforcement_mode` |

---

## 4. `workflow.instance` Views

### 4.1 Form View

**XML ID**: `view_workflow_instance_form`
**Priority**: `10`

```
┌─────────────────────────────────────────────────────┐
│ [header]                                            │
│   [button] Cancel  (invisible if terminal state)    │
│   <statusbar field="state"                          │
│     statusbar_visible="running,waiting_human,       │
│       completed_approved" />                        │
│                                                     │
│ [sheet]                                             │
│   <div class="oe_button_box">                       │
│     [stat_button] Tasks                             │
│     [stat_button] Incidents                         │
│   </div>                                            │
│                                                     │
│   <group>                                           │
│     <group string="Workflow">                       │
│       definition_id                                 │
│       definition_version_id                         │
│       state                                         │
│     </group>                                        │
│     <group string="Record">                         │
│       res_model                                     │
│       res_id                                        │
│       requester_id                                  │
│       company_id                                    │
│     </group>                                        │
│   </group>                                          │
│                                                     │
│   <group string="Timestamps">                       │
│     started_at_utc                                  │
│     ended_at_utc                                    │
│     correlation_id                                  │
│   </group>                                          │
│                                                     │
│ [chatter]                                           │
└─────────────────────────────────────────────────────┘
```

### 4.2 List View

**XML ID**: `view_workflow_instance_list`

| Column | Widget | Optional | Decoration |
|---|---|---|---|
| `name` | — | No | — |
| `definition_id` | — | No | — |
| `state` | `badge` | No | `decoration-success="state in ('completed_approved',)"`, `decoration-danger="state in ('completed_rejected','error_incident')"`, `decoration-warning="state == 'waiting_human'"` |
| `requester_id` | — | No | — |
| `started_at_utc` | — | No | — |
| `company_id` | — | Yes | — |

### 4.3 Search View

**XML ID**: `view_workflow_instance_search`

| Element | Type | Field/Domain |
|---|---|---|
| `name` | field | — |
| `definition_id` | field | — |
| `requester_id` | field | — |
| `state` | field | — |
| Running | filter | `[('state','in',['running','waiting_human','waiting_timer'])]` |
| Completed | filter | `[('state','in',['completed_approved','completed_rejected'])]` |
| Errors | filter | `[('state','=','error_incident')]` |
| By State | group_by | `state` |
| By Definition | group_by | `definition_id` |

---

## 5. `workflow.task` Views

### 5.1 Form View

**XML ID**: `view_workflow_task_form`
**Priority**: `10`

```
┌─────────────────────────────────────────────────────┐
│ [header]                                            │
│   [button] Approve  (type="object", class="oe_highlight")│
│     invisible="status not in ('pending','assigned')"│
│   [button] Reject   (type="object")                 │
│     invisible="status not in ('pending','assigned')"│
│   [button] Request Change (type="object")            │
│     invisible="status not in ('pending','assigned')"│
│   [button] Delegate (type="object")                  │
│     invisible="status not in ('pending','assigned')"│
│   <statusbar field="status"                          │
│     statusbar_visible="pending,assigned,completed" />│
│                                                     │
│ [sheet]                                             │
│   <group>                                           │
│     <group string="Assignment">                     │
│       name                                          │
│       instance_id                                   │
│       assignee_user_id                              │
│       assignee_group_id                             │
│       delegated_from_id                             │
│     </group>                                        │
│     <group string="Status">                         │
│       status                                        │
│       decision                                      │
│       sla_due_at_utc                                │
│       is_overdue (widget="boolean", decoration)     │
│       completed_at_utc                              │
│     </group>                                        │
│   </group>                                          │
│                                                     │
│   <notebook>                                        │
│     <page string="Comment">                         │
│       comment                                       │
│     </page>                                         │
│     <page string="History">                         │
│       transition_ids (list readonly)                │
│         → from_status, to_status, actor_id,         │
│           reason, occurred_at_utc                   │
│     </page>                                         │
│   </notebook>                                       │
│                                                     │
│ [chatter]                                           │
└─────────────────────────────────────────────────────┘
```

**Note**: `transition_ids` is an inverse `One2many` from `workflow.task.transition.task_id`. Add to `workflow.task` model:

```python
transition_ids = fields.One2many('workflow.task.transition', 'task_id', string='Transitions')
```

### 5.2 List View

**XML ID**: `view_workflow_task_list`

| Column | Widget | Optional | Decoration |
|---|---|---|---|
| `name` | — | No | — |
| `instance_id` | — | No | — |
| `assignee_user_id` | — | No | — |
| `status` | `badge` | No | `decoration-info="status == 'pending'"`, `decoration-success="status == 'completed'"` |
| `decision` | `badge` | Yes | — |
| `sla_due_at_utc` | — | No | — |
| `is_overdue` | `boolean` | No | `decoration-danger="is_overdue"` |

### 5.3 Kanban View

**XML ID**: `view_workflow_task_kanban`
**Default group by**: `status`

| Card Element | Content |
|---|---|
| Title | `name` |
| Subtitle | `instance_id.name` |
| Assignee | `assignee_user_id` (avatar) |
| SLA | `sla_due_at_utc` with overdue color |
| Footer | Action buttons (Approve/Reject) — visible when pending/assigned |

### 5.4 Search View

**XML ID**: `view_workflow_task_search`

| Element | Type | Field/Domain |
|---|---|---|
| `name` | field | — |
| `assignee_user_id` | field | — |
| `instance_id` | field | — |
| My Tasks | filter | `[('assignee_user_id','=',uid)]` |
| Overdue | filter | `[('is_overdue','=',True)]` |
| Pending | filter | `[('status','in',['pending','assigned'])]` |
| By Status | group_by | `status` |
| By Assignee | group_by | `assignee_user_id` |

---

## 6. `workflow.incident` Views

### 6.1 Form View

**XML ID**: `view_workflow_incident_form`
**Priority**: `10`

```
┌─────────────────────────────────────────────────────┐
│ [header]                                            │
│   [button] Triage          (invisible if != open)   │
│   [button] Retry           (invisible if != triaged)│
│   [button] Resolve         (invisible if terminal)  │
│   [button] Close Exception (invisible if terminal)  │
│   <statusbar field="state" />                        │
│                                                     │
│ [sheet]                                             │
│   <group>                                           │
│     <group string="Incident">                       │
│       name                                          │
│       category                                      │
│       severity (widget="badge")                     │
│       instance_id                                   │
│       reason_code                                   │
│     </group>                                        │
│     <group string="Resolution">                     │
│       state                                         │
│       resolution_action                             │
│       opened_at_utc                                 │
│       resolved_at_utc                               │
│       correlation_id                                │
│     </group>                                        │
│   </group>                                          │
│                                                     │
│   <group string="Details">                          │
│     description                                     │
│     resolution_note                                 │
│   </group>                                          │
│                                                     │
│ [chatter]                                           │
└─────────────────────────────────────────────────────┘
```

### 6.2 List View

**XML ID**: `view_workflow_incident_list`

| Column | Widget | Decoration |
|---|---|---|
| `name` | — | — |
| `category` | `badge` | — |
| `severity` | `badge` | `decoration-danger="severity == 'critical'"`, `decoration-warning="severity == 'high'"` |
| `state` | `badge` | — |
| `instance_id` | — | — |
| `opened_at_utc` | — | — |

### 6.3 Search View

**XML ID**: `view_workflow_incident_search`

| Element | Type | Field/Domain |
|---|---|---|
| `category` | field | — |
| `severity` | field | — |
| `state` | field | — |
| `instance_id` | field | — |
| Open | filter | `[('state','=','open')]` |
| Critical | filter | `[('severity','=','critical')]` |
| By Category | group_by | `category` |
| By Severity | group_by | `severity` |

---

## 7. `workflow.webhook.endpoint` Views

### 7.1 Form View

**XML ID**: `view_workflow_webhook_endpoint_form`

| Field | Widget | Notes |
|---|---|---|
| `name` | — | — |
| `url` | `url` | — |
| `secret` | `password` | Masked display |
| `secret_rotation_key` | `password` | Masked; visible only during rotation |
| `event_types` | — | — |
| `is_active` | `boolean_toggle` | — |
| `company_id` | — | — |

### 7.2 List View

**XML ID**: `view_workflow_webhook_endpoint_list`

| Column | Widget |
|---|---|
| `name` | — |
| `url` | `url` |
| `is_active` | `boolean_toggle` |
| `company_id` | — |

---

## 8. `workflow.outbound.event` Views

### 8.1 Form View

**XML ID**: `view_workflow_outbound_event_form`

```
┌─────────────────────────────────────────────────────┐
│ [header]                                            │
│   [button] Retry   (invisible if state != failed)   │
│   [button] Replay  (invisible if state != dead_letter)│
│                                                     │
│ [sheet]                                             │
│   <group>                                           │
│     <group>                                         │
│       event_type                                    │
│       endpoint_id                                   │
│       instance_id                                   │
│       state (widget="badge")                        │
│     </group>                                        │
│     <group>                                         │
│       attempt_count                                 │
│       last_http_status                              │
│       created_at_utc                                │
│       delivered_at_utc                              │
│       next_retry_at_utc                             │
│     </group>                                        │
│   </group>                                          │
│   <group string="Payload">                          │
│     payload (widget="ace", mode="json")             │
│     payload_hash                                    │
│     schema_version                                  │
│   </group>                                          │
│   <group string="Error">                            │
│     last_error                                      │
│   </group>                                          │
│   <group string="Tracing">                          │
│     idempotency_key                                 │
│     correlation_id                                  │
│   </group>                                          │
└─────────────────────────────────────────────────────┘
```

### 8.2 List View

**XML ID**: `view_workflow_outbound_event_list`

| Column | Widget | Decoration |
|---|---|---|
| `event_type` | — | — |
| `endpoint_id` | — | — |
| `state` | `badge` | `decoration-success="state == 'delivered'"`, `decoration-danger="state in ('failed','dead_letter')"` |
| `attempt_count` | — | — |
| `created_at_utc` | — | — |

### 8.3 Search View

**XML ID**: `view_workflow_outbound_event_search`

| Element | Type | Field/Domain |
|---|---|---|
| `event_type` | field | — |
| `endpoint_id` | field | — |
| `state` | field | — |
| Pending | filter | `[('state','=','pending')]` |
| Failed | filter | `[('state','in',['failed','dead_letter'])]` |
| By State | group_by | `state` |
| By Endpoint | group_by | `endpoint_id` |

---

## 9. `workflow.task` Kanban View

**XML ID**: `view_workflow_task_kanban`
**Priority**: `10`

**Card Layout:**

```
┌──────────────────────────┐
│  [status color stripe]   │
│  ● Task Name            │
│  👤 assignee_user_id    │
│  ⏰ sla_due_at_utc      │
│  🔴 is_overdue (badge)  │
│  Instance: instance_id  │
└──────────────────────────┘
```

| Configuration | Value |
|---|---|
| `default_group_by` | `status` |
| Column order | `pending` → `assigned` → `escalated` → `completed` → `cancelled` |
| Card fields | `name`, `assignee_user_id` (widget=many2one_avatar_user), `sla_due_at_utc`, `is_overdue` |
| Color coding | `decoration-danger` when `is_overdue == True` |
| Quick create | Disabled |

---

## 10. Deprecation Note

> The `transition_ids` and `task_ids` / `token_ids` / `decision_event_ids` / `node_runtime_ids` `One2many` fields are now declared directly on their parent models in OMB-01 (§8 and §12). Previous cross-reference notes in this document are superseded by those model field declarations.
