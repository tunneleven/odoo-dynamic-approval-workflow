# OMB-03 — `dynamic_approval_core` Security Specifications

Parent: `OMB-00-index.md`
Module: `dynamic_approval_core`
SDS Reference: `SDS §15`
DFR: `DFR-07-006`, `DFR-07-007`, `DFR-07-008`

---

## 1. Security Groups

**File**: `security/workflow_security.xml`

| XML ID | Name | Privilege | Implied By | Comment |
|---|---|---|---|---|
| `group_workflow_approver` | `Workflow Approver` | `Workflow` | `base.group_user` | Read tasks, approve/reject, view assigned instances |
| `group_workflow_designer` | `Workflow Designer` | `Workflow` | `group_workflow_approver` | Create/edit definitions, manage bindings |
| `group_workflow_admin` | `Workflow Administrator` | `Workflow` | `group_workflow_designer` | Full CRUD, manage security, resolve incidents |
| `group_workflow_auditor` | `Workflow Auditor` | `Workflow` | `base.group_user` | Read-only access to all models |

### 1.1 Category

```xml
<record id="module_category_workflow" model="ir.module.category">
    <field name="name">Workflow</field>
    <field name="description">Dynamic Approval Workflow</field>
    <field name="sequence">50</field>
</record>
```

### 1.2 Group Definitions

```xml
<record id="res_groups_privilege_workflow" model="res.groups.privilege">
    <field name="name">Workflow</field>
    <field name="category_id" ref="module_category_workflow"/>
</record>

<record id="group_workflow_approver" model="res.groups">
    <field name="name">Workflow Approver</field>
    <field name="privilege_id" ref="res_groups_privilege_workflow"/>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
    <field name="comment">Can view assigned tasks, approve/reject, view scoped instances</field>
</record>

<record id="group_workflow_designer" model="res.groups">
    <field name="name">Workflow Designer</field>
    <field name="privilege_id" ref="res_groups_privilege_workflow"/>
    <field name="implied_ids" eval="[(4, ref('group_workflow_approver'))]"/>
    <field name="comment">Can create/edit definitions, manage bindings, view all instances</field>
</record>

<record id="group_workflow_admin" model="res.groups">
    <field name="name">Workflow Administrator</field>
    <field name="privilege_id" ref="res_groups_privilege_workflow"/>
    <field name="implied_ids" eval="[(4, ref('group_workflow_designer'))]"/>
    <field name="comment">Full CRUD, manage security, resolve incidents</field>
</record>

<record id="group_workflow_auditor" model="res.groups">
    <field name="name">Workflow Auditor</field>
    <field name="privilege_id" ref="res_groups_privilege_workflow"/>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
    <field name="comment">Read-only access to all workflow models, audit events, evidence</field>
</record>
```

> Odoo 19 rule: `category_id` is valid on `res.groups.privilege` only. `res.groups` records must use `privilege_id`.

---

## 2. Access Rights (`ir.model.access.csv`)

**File**: `security/ir.model.access.csv`

Convention: `access_{model_short}_{group_short}`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_definition_approver,workflow.definition approver,model_workflow_definition,group_workflow_approver,1,0,0,0
access_definition_designer,workflow.definition designer,model_workflow_definition,group_workflow_designer,1,1,1,0
access_definition_admin,workflow.definition admin,model_workflow_definition,group_workflow_admin,1,1,1,1
access_definition_auditor,workflow.definition auditor,model_workflow_definition,group_workflow_auditor,1,0,0,0
access_definition_tag_approver,workflow.definition.tag approver,model_workflow_definition_tag,group_workflow_approver,1,0,0,0
access_definition_tag_designer,workflow.definition.tag designer,model_workflow_definition_tag,group_workflow_designer,1,1,1,1
access_definition_tag_admin,workflow.definition.tag admin,model_workflow_definition_tag,group_workflow_admin,1,1,1,1
access_definition_tag_auditor,workflow.definition.tag auditor,model_workflow_definition_tag,group_workflow_auditor,1,0,0,0
access_version_approver,workflow.definition.version approver,model_workflow_definition_version,group_workflow_approver,1,0,0,0
access_version_designer,workflow.definition.version designer,model_workflow_definition_version,group_workflow_designer,1,1,1,0
access_version_admin,workflow.definition.version admin,model_workflow_definition_version,group_workflow_admin,1,1,1,1
access_version_auditor,workflow.definition.version auditor,model_workflow_definition_version,group_workflow_auditor,1,0,0,0
access_definition_compiled_designer,workflow.definition.compiled designer,model_workflow_definition_compiled,group_workflow_designer,1,0,0,0
access_definition_compiled_admin,workflow.definition.compiled admin,model_workflow_definition_compiled,group_workflow_admin,1,1,1,1
access_definition_compiled_auditor,workflow.definition.compiled auditor,model_workflow_definition_compiled,group_workflow_auditor,1,0,0,0
access_binding_approver,workflow.binding approver,model_workflow_binding,group_workflow_approver,1,0,0,0
access_binding_designer,workflow.binding designer,model_workflow_binding,group_workflow_designer,1,1,1,0
access_binding_admin,workflow.binding admin,model_workflow_binding,group_workflow_admin,1,1,1,1
access_binding_auditor,workflow.binding auditor,model_workflow_binding,group_workflow_auditor,1,0,0,0
access_binding_scope_designer,workflow.binding.scope designer,model_workflow_binding_scope,group_workflow_designer,1,1,1,1
access_binding_scope_admin,workflow.binding.scope admin,model_workflow_binding_scope,group_workflow_admin,1,1,1,1
access_binding_scope_auditor,workflow.binding.scope auditor,model_workflow_binding_scope,group_workflow_auditor,1,0,0,0
access_instance_approver,workflow.instance approver,model_workflow_instance,group_workflow_approver,1,0,0,0
access_instance_designer,workflow.instance designer,model_workflow_instance,group_workflow_designer,1,1,0,0
access_instance_admin,workflow.instance admin,model_workflow_instance,group_workflow_admin,1,1,1,1
access_instance_auditor,workflow.instance auditor,model_workflow_instance,group_workflow_auditor,1,0,0,0
access_node_runtime_approver,workflow.node.runtime approver,model_workflow_node_runtime,group_workflow_approver,1,0,0,0
access_node_runtime_admin,workflow.node.runtime admin,model_workflow_node_runtime,group_workflow_admin,1,1,1,1
access_node_runtime_auditor,workflow.node.runtime auditor,model_workflow_node_runtime,group_workflow_auditor,1,0,0,0
access_token_admin,workflow.token admin,model_workflow_token,group_workflow_admin,1,1,1,0
access_token_auditor,workflow.token auditor,model_workflow_token,group_workflow_auditor,1,0,0,0
access_decision_event_approver,workflow.decision.event approver,model_workflow_decision_event,group_workflow_approver,1,0,1,0
access_decision_event_admin,workflow.decision.event admin,model_workflow_decision_event,group_workflow_admin,1,1,1,0
access_decision_event_auditor,workflow.decision.event auditor,model_workflow_decision_event,group_workflow_auditor,1,0,0,0
access_task_approver,workflow.task approver,model_workflow_task,group_workflow_approver,1,1,0,0
access_task_designer,workflow.task designer,model_workflow_task,group_workflow_designer,1,1,0,0
access_task_admin,workflow.task admin,model_workflow_task,group_workflow_admin,1,1,1,1
access_task_auditor,workflow.task auditor,model_workflow_task,group_workflow_auditor,1,0,0,0
access_task_transition_approver,workflow.task.transition approver,model_workflow_task_transition,group_workflow_approver,1,0,0,0
access_task_transition_admin,workflow.task.transition admin,model_workflow_task_transition,group_workflow_admin,1,0,1,0
access_task_transition_auditor,workflow.task.transition auditor,model_workflow_task_transition,group_workflow_auditor,1,0,0,0
access_approver_resolution_designer,workflow.approver.resolution designer,model_workflow_approver_resolution,group_workflow_designer,1,1,1,1
access_approver_resolution_admin,workflow.approver.resolution admin,model_workflow_approver_resolution,group_workflow_admin,1,1,1,1
access_approver_resolution_auditor,workflow.approver.resolution auditor,model_workflow_approver_resolution,group_workflow_auditor,1,0,0,0
access_delegation_record_approver,workflow.delegation.record approver,model_workflow_delegation_record,group_workflow_approver,1,1,1,0
access_delegation_record_admin,workflow.delegation.record admin,model_workflow_delegation_record,group_workflow_admin,1,1,1,1
access_delegation_record_auditor,workflow.delegation.record auditor,model_workflow_delegation_record,group_workflow_auditor,1,0,0,0
access_follower_rule_designer,workflow.follower.rule designer,model_workflow_follower_rule,group_workflow_designer,1,1,1,1
access_follower_rule_admin,workflow.follower.rule admin,model_workflow_follower_rule,group_workflow_admin,1,1,1,1
access_follower_rule_auditor,workflow.follower.rule auditor,model_workflow_follower_rule,group_workflow_auditor,1,0,0,0
access_condition_rule_designer,workflow.condition.rule designer,model_workflow_condition_rule,group_workflow_designer,1,1,1,1
access_condition_rule_admin,workflow.condition.rule admin,model_workflow_condition_rule,group_workflow_admin,1,1,1,1
access_condition_rule_auditor,workflow.condition.rule auditor,model_workflow_condition_rule,group_workflow_auditor,1,0,0,0
access_signature_evidence_approver,workflow.signature.evidence approver,model_workflow_signature_evidence,group_workflow_approver,1,0,1,0
access_signature_evidence_admin,workflow.signature.evidence admin,model_workflow_signature_evidence,group_workflow_admin,1,0,1,0
access_signature_evidence_auditor,workflow.signature.evidence auditor,model_workflow_signature_evidence,group_workflow_auditor,1,0,0,0
access_attestation_policy_designer,workflow.attestation.policy designer,model_workflow_attestation_policy,group_workflow_designer,1,1,1,1
access_attestation_policy_admin,workflow.attestation.policy admin,model_workflow_attestation_policy,group_workflow_admin,1,1,1,1
access_attestation_policy_auditor,workflow.attestation.policy auditor,model_workflow_attestation_policy,group_workflow_auditor,1,0,0,0
access_access_grant_approver,workflow.access.grant approver,model_workflow_access_grant,group_workflow_approver,1,0,0,0
access_access_grant_admin,workflow.access.grant admin,model_workflow_access_grant,group_workflow_admin,1,1,1,1
access_access_grant_auditor,workflow.access.grant auditor,model_workflow_access_grant,group_workflow_auditor,1,0,0,0
access_access_grant_log_admin,workflow.access.grant.log admin,model_workflow_access_grant_log,group_workflow_admin,1,0,1,0
access_access_grant_log_auditor,workflow.access.grant.log auditor,model_workflow_access_grant_log,group_workflow_auditor,1,0,0,0
access_notification_template_admin,workflow.notification.template admin,model_workflow_notification_template,group_workflow_admin,1,1,1,1
access_notification_template_auditor,workflow.notification.template auditor,model_workflow_notification_template,group_workflow_auditor,1,0,0,0
access_notification_log_approver,workflow.notification.log approver,model_workflow_notification_log,group_workflow_approver,1,0,0,0
access_notification_log_admin,workflow.notification.log admin,model_workflow_notification_log,group_workflow_admin,1,1,1,0
access_notification_log_auditor,workflow.notification.log auditor,model_workflow_notification_log,group_workflow_auditor,1,0,0,0
access_webhook_endpoint_admin,workflow.webhook.endpoint admin,model_workflow_webhook_endpoint,group_workflow_admin,1,1,1,1
access_webhook_endpoint_auditor,workflow.webhook.endpoint auditor,model_workflow_webhook_endpoint,group_workflow_auditor,1,0,0,0
access_outbound_event_admin,workflow.outbound.event admin,model_workflow_outbound_event,group_workflow_admin,1,1,1,0
access_outbound_event_auditor,workflow.outbound.event auditor,model_workflow_outbound_event,group_workflow_auditor,1,0,0,0
access_idempotency_registry_admin,workflow.idempotency.registry admin,model_workflow_idempotency_registry,group_workflow_admin,1,1,1,0
access_idempotency_auditor,workflow.idempotency.registry auditor,model_workflow_idempotency_registry,group_workflow_auditor,1,0,0,0
access_incident_approver,workflow.incident approver,model_workflow_incident,group_workflow_approver,1,0,0,0
access_incident_admin,workflow.incident admin,model_workflow_incident,group_workflow_admin,1,1,1,0
access_incident_auditor,workflow.incident auditor,model_workflow_incident,group_workflow_auditor,1,0,0,0
access_audit_event_approver,workflow.audit.event approver,model_workflow_audit_event,group_workflow_approver,1,0,0,0
access_audit_event_admin,workflow.audit.event admin,model_workflow_audit_event,group_workflow_admin,1,0,1,0
access_audit_event_auditor,workflow.audit.event auditor,model_workflow_audit_event,group_workflow_auditor,1,0,0,0
```

**Total**: 78 ACL rows covering 28 concrete models × 4 groups.

### 2.1 ACL Design Principles

| Group | Default Permissions | Exceptions |
|---|---|---|
| `approver` | Read on most models | Write on `workflow.task` (for approve/reject); Create on `workflow.decision.event` and `workflow.signature.evidence` |
| `designer` | Read + Write + Create on definition/version/binding/resolution/condition/follower/attestation | No unlink on definitions, versions, bindings |
| `admin` | Full CRUD | No unlink on audit events, tokens, transitions |
| `auditor` | Read-only everywhere | No write/create/unlink on anything |

---

## 3. Record Rules (`ir.rule`)

**File**: `security/workflow_security.xml`

### 3.1 Multi-Company Rules (Global)

These apply to **all users** (no group restriction) and enforce company isolation per SDS §9.

| XML ID | Model | Domain | Global | Comment |
|---|---|---|---|---|
| `rule_definition_company` | `workflow.definition` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_version_company` | `workflow.definition.version` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_compiled_company` | `workflow.definition.compiled` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_binding_company` | `workflow.binding` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_binding_scope_company` | `workflow.binding.scope` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_instance_company` | `workflow.instance` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_node_runtime_company` | `workflow.node.runtime` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_token_company` | `workflow.token` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_decision_event_company` | `workflow.decision.event` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_task_company` | `workflow.task` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_task_transition_company` | `workflow.task.transition` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_delegation_company` | `workflow.delegation.record` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_signature_evidence_company` | `workflow.signature.evidence` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_access_grant_company` | `workflow.access.grant` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_access_grant_log_company` | `workflow.access.grant.log` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_notification_template_company` | `workflow.notification.template` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_notification_log_company` | `workflow.notification.log` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_webhook_endpoint_company` | `workflow.webhook.endpoint` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_outbound_event_company` | `workflow.outbound.event` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_idempotency_company` | `workflow.idempotency.registry` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_incident_company` | `workflow.incident` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |
| `rule_audit_event_company` | `workflow.audit.event` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes | — |

### 3.2 Role-Based Rules

| XML ID | Model | Domain | Groups | Perm | Comment |
|---|---|---|---|---|---|
| `rule_task_approver_assigned` | `workflow.task` | `['|',('assignee_user_id','=',user.id),('assignee_group_id','in',user.groups_id.ids)]` | `group_workflow_approver` | Read, Write | Approvers see only their assigned tasks |
| `rule_instance_approver_has_task` | `workflow.instance` | `[('id','in',user_task_instance_ids)]` | `group_workflow_approver` | Read | Approvers see instances where they have tasks |
| `rule_access_grant_user` | `workflow.access.grant` | `[('user_id','=',user.id)]` | `group_workflow_approver` | Read | Approvers see their own grants |

**Note**: `user_task_instance_ids` requires a computed sub-select or Python domain. Implementation can use `@api.model` method domain or SQL-based `ir.rule`.

### 3.3 Access Grant Dynamic Rule

For enabling temporary record access via grants (SDS §11):

```xml
<record id="rule_access_grant_dynamic" model="ir.rule">
    <field name="name">Workflow Access Grant - Dynamic Read</field>
    <field name="model_id" eval="False"/>  <!-- Applied programmatically per model -->
    <field name="domain_force">
        [('id','in', active_grant_record_ids)]
    </field>
    <field name="groups" eval="[(4, ref('group_workflow_approver'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="False"/>
    <field name="perm_create" eval="False"/>
    <field name="perm_unlink" eval="False"/>
</record>
```

**Implementation Note**: Dynamic grant rules are created programmatically by the `workflow.access.grant` model when grants are provisioned. The rule domain references active grants for the current user on the target model. Cache invalidation is required on grant create/revoke.

---

## 4. Permission Matrix Summary

| Model | Approver | Designer | Admin | Auditor |
|---|---|---|---|---|
| `workflow.definition` | R | RWC | RWCD | R |
| `workflow.definition.tag` | R | RWCD | RWCD | R |
| `workflow.definition.version` | R | RWC | RWCD | R |
| `workflow.definition.compiled` | — | R | RWCD | R |
| `workflow.binding` | R | RWC | RWCD | R |
| `workflow.binding.scope` | — | RWCD | RWCD | R |
| `workflow.instance` | R* | RW | RWCD | R |
| `workflow.node.runtime` | R | — | RWCD | R |
| `workflow.token` | — | — | RWC | R |
| `workflow.decision.event` | RC | — | RWC | R |
| `workflow.task` | RW* | RW | RWCD | R |
| `workflow.task.transition` | R | — | RC | R |
| `workflow.approver.resolution` | — | RWCD | RWCD | R |
| `workflow.delegation.record` | RWC | — | RWCD | R |
| `workflow.follower.rule` | — | RWCD | RWCD | R |
| `workflow.condition.rule` | — | RWCD | RWCD | R |
| `workflow.signature.evidence` | RC | — | RC | R |
| `workflow.attestation.policy` | — | RWCD | RWCD | R |
| `workflow.access.grant` | R* | — | RWCD | R |
| `workflow.access.grant.log` | — | — | RC | R |
| `workflow.notification.template` | — | — | RWCD | R |
| `workflow.notification.log` | R | — | RWC | R |
| `workflow.webhook.endpoint` | — | — | RWCD | R |
| `workflow.outbound.event` | — | — | RWC | R |
| `workflow.idempotency.registry` | — | — | RWC | R |
| `workflow.incident` | R | — | RWC | R |
| `workflow.audit.event` | R | — | RC | R |

**Legend**: R=Read, W=Write, C=Create, D=Delete. `*` = record-rule restricted (own tasks/instances/grants).
