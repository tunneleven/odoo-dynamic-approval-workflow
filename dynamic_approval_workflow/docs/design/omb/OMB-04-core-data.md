# OMB-04 — `dynamic_approval_core` Data, Cron, Mail Templates, and Demo

Parent: `OMB-00-index.md`
Module: `dynamic_approval_core`
SDS Reference: `SDS §6.3` (Hybrid Scheduler)

---

## 1. Cron Jobs

**File**: `data/ir_cron_data.xml`

| XML ID | Name | Model | Method | Interval | Active | Groups | DFR/SDS |
|---|---|---|---|---|---|---|---|
| `ir_cron_timer_discovery` | `Workflow: Discover Expired Timers` | `workflow.node.runtime` | `_cron_discover_expired_timers` | 1 minute | Yes | — | SDS §6.3 |
| `ir_cron_sla_checker` | `Workflow: Check SLA Deadlines` | `workflow.task` | `_cron_check_sla` | 5 minutes | Yes | — | `DFR-05-011` |
| `ir_cron_deadline_checker` | `Workflow: Check Task Deadlines` | `workflow.task` | `_cron_check_deadlines` | 5 minutes | Yes | — | `DFR-04-009` |
| `ir_cron_grant_expiry` | `Workflow: Expire Access Grants` | `workflow.access.grant` | `_cron_expire_grants` | 5 minutes | Yes | — | `DFR-07-003` |
| `ir_cron_grant_reconciliation` | `Workflow: Reconcile Orphan Grants` | `workflow.access.grant` | `_cron_reconcile_orphan_grants` | 1 hour | Yes | — | SDS §11.2 |
| `ir_cron_idempotency_purge` | `Workflow: Purge Expired Idempotency Keys` | `workflow.idempotency.registry` | `_cron_purge_expired` | 1 day | Yes | — | SDS §10.5 |

### 1.1 Cron Record Template

```xml
<record id="ir_cron_timer_discovery" model="ir.cron">
    <field name="name">Workflow: Discover Expired Timers</field>
    <field name="model_id" ref="model_workflow_node_runtime"/>
    <field name="state">code</field>
    <field name="code">model._cron_discover_expired_timers()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">minutes</field>
    <field name="active" eval="True"/>
</record>
```

### 1.2 Cron Method Signatures

| Model | Method | Description | Idempotent |
|---|---|---|---|
| `workflow.node.runtime` | `_cron_discover_expired_timers()` | Find `active` timer nodes past deadline; enqueue execution via `queue_job` | Yes |
| `workflow.task` | `_cron_check_sla()` | Scan tasks approaching/past SLA; update `is_overdue`; trigger notifications | Yes |
| `workflow.task` | `_cron_check_deadlines()` | Apply timeout policies (`auto-approve`, `auto-reject`, `escalate-only`) | Yes |
| `workflow.access.grant` | `_cron_expire_grants()` | Transition `active` grants past `expires_at_utc` to `expired`; log | Yes |
| `workflow.access.grant` | `_cron_reconcile_orphan_grants()` | Find `active` grants for completed/cancelled tasks; revoke | Yes |
| `workflow.idempotency.registry` | `_cron_purge_expired()` | Delete entries past `expires_at_utc` | Yes |

> **Cross-reference:** Method signatures above correspond to the business method tables in OMB-01: `_cron_check_sla` (§12), `_cron_check_deadlines` (§12), `_cron_expire_grants` (§20), `_cron_reconcile_orphan_grants` (§20), `_cron_purge_expired` (§26), and `_cron_discover_expired_timers` (§9).

---

## 2. System Parameters

**File**: `data/workflow_data.xml`

| XML ID | Key | Default | DFR/SDS |
|---|---|---|---|
| `param_lock_timeout` | `workflow.lock_timeout_seconds` | `10` | SDS §6.4 |
| `param_lock_retry_count` | `workflow.lock_retry_count` | `3` | SDS §6.4 |
| `param_lock_backoff_base_ms` | `workflow.lock_backoff_base_ms` | `100` | SDS §6.4 |
| `param_lock_backoff_factor` | `workflow.lock_backoff_factor` | `2` | SDS §6.4 |
| `param_lock_backoff_cap_ms` | `workflow.lock_backoff_cap_ms` | `800` | SDS §6.4 |
| `param_grant_default_ttl_hours` | `workflow.grant_default_ttl_hours` | `24` | SDS §11.2 |
| `param_idempotency_ttl_days` | `workflow.idempotency_ttl_days` | `90` | SDS §10.5 (interim) |
| `param_rework_max_loops` | `workflow.rework_max_loops` | `5` | `DFR-04-005` |
| `param_webhook_replay_window_seconds` | `workflow.webhook_replay_window_seconds` | `300` | SDS §12.2 |
| `param_callback_max_depth` | `workflow.callback_max_depth` | `3` | `DFR-02-013` |

### 2.1 Data Record Template

```xml
<record id="param_lock_timeout" model="ir.config_parameter">
    <field name="key">workflow.lock_timeout_seconds</field>
    <field name="value">10</field>
</record>
```

---

## 3. Mail Templates

**File**: `data/mail_template_data.xml`

| XML ID | Name | Model | Event Type | Subject Pattern | DFR |
|---|---|---|---|---|---|
| `mail_template_task_assigned` | `Workflow: Task Assigned` | `workflow.task` | `task_assigned` | `Approval Required: ${object.name}` | `DFR-08-001` |
| `mail_template_task_reminder` | `Workflow: Task Reminder` | `workflow.task` | `task_reminder` | `Reminder: ${object.name} - Due ${object.sla_due_at_utc}` | `DFR-08-001` |
| `mail_template_task_escalated` | `Workflow: Task Escalated` | `workflow.task` | `task_escalated` | `Escalation: ${object.name}` | `DFR-08-001` |
| `mail_template_instance_approved` | `Workflow: Instance Approved` | `workflow.instance` | `instance_approved` | `Approved: ${object.name}` | `DFR-08-002` |
| `mail_template_instance_rejected` | `Workflow: Instance Rejected` | `workflow.instance` | `instance_rejected` | `Rejected: ${object.name}` | `DFR-08-002` |
| `mail_template_sla_warning` | `Workflow: SLA Warning` | `workflow.task` | `sla_warning` | `SLA Warning: ${object.name}` | `DFR-05-011` |

### 3.1 Mail Template Record

```xml
<record id="mail_template_task_assigned" model="mail.template">
    <field name="name">Workflow: Task Assigned</field>
    <field name="model_id" ref="model_workflow_task"/>
    <field name="subject">Approval Required: ${object.name}</field>
    <field name="body_html" type="html">
        <div style="margin: 0px; padding: 0px;">
            <p>Hello ${object.assignee_user_id.name or ''},</p>
            <p>You have been assigned an approval task:</p>
            <ul>
                <li><strong>Task:</strong> ${object.name}</li>
                <li><strong>Workflow:</strong> ${object.instance_id.definition_id.name}</li>
                <li><strong>Due:</strong> ${object.sla_due_at_utc or 'No deadline'}</li>
            </ul>
            <p>Please review and take action.</p>
        </div>
    </field>
    <field name="email_from">${(object.company_id.email or 'noreply@example.com')}</field>
    <field name="email_to">${object.assignee_user_id.email or ''}</field>
    <field name="auto_delete" eval="True"/>
</record>
```

---

## 4. Default Notification Templates (Data)

**File**: `data/workflow_data.xml`

Pre-create default `workflow.notification.template` records linking to the mail templates above:

| XML ID | Event Type | Channel | Mail Template Ref | Active |
|---|---|---|---|---|
| `notification_tmpl_task_assigned_inbox` | `task_assigned` | `inbox` | — | Yes |
| `notification_tmpl_task_assigned_email` | `task_assigned` | `email` | `mail_template_task_assigned` | Yes |
| `notification_tmpl_task_reminder_inbox` | `task_reminder` | `inbox` | — | Yes |
| `notification_tmpl_task_reminder_email` | `task_reminder` | `email` | `mail_template_task_reminder` | Yes |
| `notification_tmpl_task_escalated_inbox` | `task_escalated` | `inbox` | — | Yes |
| `notification_tmpl_instance_approved_inbox` | `instance_approved` | `inbox` | — | Yes |
| `notification_tmpl_instance_approved_email` | `instance_approved` | `email` | `mail_template_instance_approved` | Yes |
| `notification_tmpl_instance_rejected_inbox` | `instance_rejected` | `inbox` | — | Yes |
| `notification_tmpl_instance_rejected_email` | `instance_rejected` | `email` | `mail_template_instance_rejected` | Yes |
| `notification_tmpl_sla_warning_email` | `sla_warning` | `email` | `mail_template_sla_warning` | Yes |

### 4.1 Template Record

```xml
<record id="notification_tmpl_task_assigned_email" model="workflow.notification.template">
    <field name="name">Task Assigned (Email)</field>
    <field name="event_type">task_assigned</field>
    <field name="channel">email</field>
    <field name="mail_template_id" ref="mail_template_task_assigned"/>
    <field name="is_active" eval="True"/>
    <field name="company_id" ref="base.main_company"/>
</record>
```

---

## 5. Demo Data

**File**: `demo/workflow_demo.xml`
**Condition**: Only loaded when `--demo` flag is set (standard Odoo convention via `__manifest__.py` `demo` key).

### 5.1 Demo Records

| XML ID | Model | Key Data |
|---|---|---|
| `demo_definition_purchase` | `workflow.definition` | `name='Purchase Approval'`, `definition_key='purchase_approval'` |
| `demo_definition_expense` | `workflow.definition` | `name='Expense Approval'`, `definition_key='expense_approval'` |
| `demo_version_purchase_v1` | `workflow.definition.version` | `definition_id=demo_definition_purchase`, `state='published'`, `version=1` |
| `demo_version_expense_v1` | `workflow.definition.version` | `definition_id=demo_definition_expense`, `state='draft'` |
| `demo_binding_purchase_confirm` | `workflow.binding` | `definition_id=demo_definition_purchase`, `target_model='purchase.order'`, `target_action_method='button_confirm'`, `enforcement_mode='orm_enforced'` |
| `demo_approver_rule_purchase` | `workflow.approver.resolution` | `definition_version_id=demo_version_purchase_v1`, `node_id='UserTask_1'`, `resolution_type='group'`, `group_id=base.group_purchase_manager` |
| `demo_delegation_record` | `workflow.delegation.record` | Example delegation window |
| `demo_webhook_endpoint` | `workflow.webhook.endpoint` | `name='Dev Webhook'`, `url='https://httpbin.org/post'` |

### 5.2 Demo User Assignments

| XML ID | Model | Purpose |
|---|---|---|
| `demo_user_designer` | `res.users` | User with `group_workflow_designer` |
| `demo_user_approver_1` | `res.users` | User with `group_workflow_approver` |
| `demo_user_approver_2` | `res.users` | User with `group_workflow_approver` |
| `demo_user_auditor` | `res.users` | User with `group_workflow_auditor` |

---

## 6. `__manifest__.py` Data Key Structure

```python
{
    'data': [
        'security/workflow_security.xml',
        'security/ir.model.access.csv',
        'data/workflow_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/workflow_definition_views.xml',
        'views/workflow_binding_views.xml',
        'views/workflow_instance_views.xml',
        'views/workflow_task_views.xml',
        'views/workflow_incident_views.xml',
        'views/workflow_webhook_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/workflow_demo.xml',
    ],
}
```
