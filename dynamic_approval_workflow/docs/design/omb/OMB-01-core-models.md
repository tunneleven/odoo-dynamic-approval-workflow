# OMB-01 — `dynamic_approval_core` Model Specifications

Parent: `OMB-00-index.md`
Module: `dynamic_approval_core`
Models: 28 concrete + 2 abstract = 30 total

---

## 1. `workflow.definition`

**File**: `models/workflow_definition.py`
**Inherits**: `mail.thread`, `mail.activity.mixin`
**Description**: Stable workflow definition header with ownership metadata.
**DFR**: `DFR-01-001`, `DFR-01-002`, `DFR-01-008`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Name` | `Human-readable definition name` | — |
| `definition_key` | `Char(64)` | Yes | — | Yes | After first publish | `Definition Key` | `Unique slug identifier` | Regex `^[a-z][a-z0-9_]{2,63}$`; `copy=False` |
| `description` | `Text` | No | — | — | — | `Description` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | Multi-company isolation |
| `tag_ids` | `Many2many('workflow.definition.tag')` | No | — | — | — | `Tags` | — | — |
| `version_ids` | `One2many('workflow.definition.version', 'definition_id')` | — | — | — | — | `Versions` | — | — |
| `version_count` | `Integer` | — | — | — | Yes | `Version Count` | — | `compute='_compute_version_count'`, stored |
| `active` | `Boolean` | — | `True` | — | — | `Active` | — | Odoo archive mechanism |

**SQL Constraints**:

```python
_unique_company_key = models.Constraint(
    'UNIQUE(company_id, definition_key)',
    'Definition key must be unique per company.',
)
```

**Python Constraints**:

```python
@api.constrains('definition_key')
def _check_definition_key_format(self):
    """Validate key matches ^[a-z][a-z0-9_]{2,63}$."""
```

**Computed Methods**:

| Method | Dependencies | Logic |
|---|---|---|
| `_compute_version_count` | `version_ids` | `len(self.version_ids)` |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_create_draft` | — | `workflow.definition.version` action | `DFR-01-001` |

**CRUD Overrides**:

| Method | Reason |
|---|---|
| `unlink` | Block if any version/audit history exists |

---

## 2. `workflow.definition.tag`

**File**: `models/workflow_definition.py` (same file, helper model)
**Description**: Tagging taxonomy for definitions.

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(64)` | Yes | — | — | — | `Tag Name` | — | — |
| `color` | `Integer` | No | `0` | — | — | `Color` | — | Odoo color index 0–11 |

---

## 3. `workflow.definition.version`

**File**: `models/workflow_definition_version.py`
**Inherits**: `mail.thread`
**Description**: Versioned record with lifecycle state and immutable publish payload.
**DFR**: `DFR-01-002`, `DFR-01-003`, `DFR-01-004`, `DFR-01-005`, `DFR-01-006`, `DFR-01-010`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `definition_id` | `Many2one('workflow.definition')` | Yes | — | Yes | Yes | `Definition` | — | `ondelete='cascade'` |
| `version` | `Integer` | — | — | Yes | Yes | `Version` | `Monotonic version number` | Assigned at publish; auto-incremented per `(company_id, definition_id)` |
| `state` | `Selection` | Yes | `draft` | Yes | — | `Status` | — | Values: `draft`, `published`, `archived` |
| `bpmn_xml` | `Text` | No | — | — | After publish | `BPMN XML` | `Canonical BPMN 2.0 XML source` | Immutable when `state=published` |
| `bpmn_hash` | `Char(64)` | No | — | Yes | Yes | `BPMN Hash` | `SHA-256 of canonical XML` | Computed at publish |
| `effective_from_utc` | `Datetime` | No | — | Yes | — | `Effective From` | `UTC activation start` | Required at publish |
| `effective_to_utc` | `Datetime` | No | — | — | — | `Effective To` | `UTC activation end (exclusive)` | Must be > `effective_from_utc` if set |
| `published_at_utc` | `Datetime` | No | — | — | Yes | `Published At` | — | Set at publish |
| `published_by_id` | `Many2one('res.users')` | No | — | — | Yes | `Published By` | — | `ondelete='set null'`; set at publish |
| `source_version_id` | `Many2one('workflow.definition.version')` | No | — | — | Yes | `Cloned From` | — | `ondelete='set null'`; set by clone operation |
| `draft_revision` | `Integer` | — | `1` | — | — | `Draft Revision` | `Optimistic lock token` | Incremented on each save |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='definition_id.company_id'`, `store=True` |
| `compiled_id` | `Many2one('workflow.definition.compiled')` | No | — | — | Yes | `Compiled Artifact` | — | `ondelete='set null'`; set at publish/compile |
| `active` | `Boolean` | — | `True` | — | — | `Active` | — | — |

**SQL Constraints**:

```python
_unique_version_per_definition = models.Constraint(
    'UNIQUE(definition_id, version)',
    'Version number must be unique per definition.',
)
```

**Python Constraints**:

```python
@api.constrains('effective_from_utc', 'effective_to_utc')
def _check_effective_window(self):
    """effective_to_utc must be > effective_from_utc when both set."""

@api.constrains('state', 'effective_from_utc')
def _check_publish_requires_effective(self):
    """Published versions must have effective_from_utc."""
```

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_validate` | — | Validation result dict | `DFR-01-005` |
| `action_publish` | `effective_from_utc`, `effective_to_utc=None`, `idempotency_key=None` | `self` | `DFR-01-005`, `DFR-01-006` |
| `action_archive` | — | `self` | `DFR-01-002` |
| `action_clone` | — | New draft `workflow.definition.version` | `DFR-01-004` |
| `_resolve_version` | `start_context: dict` | `workflow.definition.version` or raise | `DFR-01-009` |
| `_assign_next_version_number` | — | `int` | `DFR-01-003` |

**CRUD Overrides**:

| Method | Reason |
|---|---|
| `write` | Block immutable fields when `state=published` (`bpmn_xml`, `bpmn_hash`, `version`, `published_at_utc`, `published_by_id`) |

---

## 4. `workflow.definition.compiled`

**File**: `models/workflow_definition_compiled.py`
**Description**: Deterministic runtime artifact derived from canonical BPMN XML.
**DFR**: `DFR-01-005`, `DFR-03-003`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `bpmn_hash` | `Char(64)` | Yes | — | Yes | Yes | `BPMN Hash` | `SHA-256 of source XML` | — |
| `compiled_data` | `Text` | Yes | — | — | Yes | `Compiled Data` | `JSON runtime artifact` | Valid JSON |
| `node_count` | `Integer` | No | — | — | Yes | `Node Count` | — | — |
| `gateway_count` | `Integer` | No | — | — | Yes | `Gateway Count` | — | — |
| `compiled_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Compiled At` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | — |

**SQL Constraints**:

```python
_unique_hash_company = models.Constraint(
    'UNIQUE(bpmn_hash, company_id)',
    'Compiled artifact must be unique per BPMN hash and company.',
)
```

---

## 5. `workflow.binding`

**File**: `models/workflow_binding.py`
**Inherits**: `mail.thread`
**Description**: Binds a workflow definition to a target model+method with enforcement and callback configuration.
**DFR**: `DFR-02-001`, `DFR-02-002`, `DFR-02-005`, `DFR-02-009`, `DFR-02-012`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Name` | — | — |
| `definition_id` | `Many2one('workflow.definition')` | Yes | — | Yes | — | `Definition` | — | `ondelete='restrict'` |
| `target_model` | `Char(128)` | Yes | — | Yes | After enable | `Target Model` | — | Must match installed `ir.model` `_name` |
| `target_action_method` | `Char(64)` | Yes | — | Yes | After enable | `Target Method` | — | Regex `^[a-z_][a-z0-9_]*$` |
| `enforcement_mode` | `Selection` | Yes | `orm_enforced` | Yes | — | `Enforcement Mode` | — | `orm_enforced`, `hybrid`, `ui_only` |
| `compliance_critical` | `Boolean` | — | `False` | — | — | `Compliance Critical` | — | `ui_only` forbidden when `True` |
| `callback_model` | `Char(128)` | Cond | — | — | — | `Callback Model` | — | Required with `callback_method` |
| `callback_method` | `Char(64)` | Cond | — | — | — | `Callback Method` | — | Regex `^[a-z_][a-z0-9_]*$` |
| `callback_execution_principal` | `Selection` | Cond | `request_actor` | — | — | `Callback Principal` | — | `request_actor`, `approver_actor`, `service_principal` |
| `callback_service_user_id` | `Many2one('res.users')` | Cond | — | — | — | `Service User` | — | `ondelete='restrict'`; required when principal = `service_principal` |
| `callback_idempotency_policy` | `Selection` | — | `strict_once` | — | — | `Callback Idempotency` | — | `strict_once`, `allow_safe_replay` |
| `is_active` | `Boolean` | — | `False` | — | — | `Active` | — | Enable only after validation |
| `binding_priority` | `Integer` | — | `100` | — | — | `Priority` | `Higher wins within same specificity` | — |
| `ui_warning_message` | `Char(255)` | No | — | — | — | `Warning Message` | `Shown for allowed_with_warning` | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | — |
| `scope_ids` | `One2many('workflow.binding.scope', 'binding_id')` | — | — | — | — | `Scopes` | — | — |
| `interceptor_config_revision` | `Integer` | — | `0` | — | Yes | `Config Revision` | `Monotonic counter for cache refresh` | Auto-incremented on change |

**SQL Constraints**:

```python
_unique_model_method_company = models.Constraint(
    'UNIQUE(target_model, target_action_method, company_id)',
    'Binding must be unique per model, method, and company.',
)
```

**Python Constraints**:

```python
@api.constrains('enforcement_mode', 'compliance_critical')
def _check_ui_only_not_compliance(self):
    """ui_only is forbidden for compliance_critical bindings."""

@api.constrains('callback_model', 'callback_method')
def _check_callback_pair(self):
    """callback_model and callback_method must both be set or both empty."""

@api.constrains('callback_execution_principal', 'callback_service_user_id')
def _check_service_principal_user(self):
    """service_principal requires callback_service_user_id."""

@api.constrains('target_action_method', 'callback_method')
def _check_method_format(self):
    """Method names must match ^[a-z_][a-z0-9_]*$."""
```

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_validate` | — | Validation result dict | `DFR-02-001` |
| `action_enable` | — | `self` | `DFR-02-005` |
| `action_disable` | — | `self` | `DFR-02-005` |
| `evaluate_gate` | `record_context: dict` | Gate response dict | `DFR-02-002`, `DFR-02-008` |
| `execute_callback` | `instance_id, payload, idempotency_key` | Result dict | `DFR-02-012` |
| `_increment_config_revision` | — | — | `DFR-02-015` |

---

## 6. `workflow.binding.scope`

**File**: `models/workflow_binding_scope.py`
**Description**: Rollout scope values for binding precedence evaluation.
**DFR**: `DFR-02-004`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `binding_id` | `Many2one('workflow.binding')` | Yes | — | Yes | — | `Binding` | — | `ondelete='cascade'` |
| `scope_type` | `Selection` | Yes | — | — | — | `Scope Type` | — | `company`, `group`, `domain` |
| `scope_company_id` | `Many2one('res.company')` | Cond | — | — | — | `Scope Company` | — | Required when `scope_type=company` |
| `scope_group_id` | `Many2one('res.groups')` | Cond | — | — | — | `Scope Group` | — | Required when `scope_type=group` |
| `scope_domain` | `Text` | Cond | — | — | — | `Scope Domain` | `JSON domain expression` | Required when `scope_type=domain`; validated for syntax + field existence |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='binding_id.company_id'`, `store=True` |

**Python Constraints**:

```python
@api.constrains('scope_type', 'scope_company_id', 'scope_group_id', 'scope_domain')
def _check_scope_value_required(self):
    """Validate scope value matches scope_type."""
```

---

## 7. `workflow.enforcement.interceptor`

**File**: `models/workflow_enforcement_interceptor.py`
**Description**: Abstract model implementing `_patch_method` enforcement. No database table.
**DFR**: `DFR-02-010`, `DFR-02-015`

```python
_name = 'workflow.enforcement.interceptor'
_description = 'Workflow Enforcement Interceptor'
_auto = False  # AbstractModel — no table
```

**Class Methods** (not instance methods):

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `_apply_patches` | `registry` | — | `DFR-02-015` |
| `_remove_patches` | `registry` | — | `DFR-02-015` |
| `_build_wrapper` | `model_name, method_name` | Wrapper function | `DFR-02-010` |
| `_resolve_binding` | `model_name, method_name, company_id` | `workflow.binding` or `None` | `DFR-02-001` |

---

## 8. `workflow.instance`

**File**: `models/workflow_instance.py`
**Inherits**: `mail.thread`
**Description**: Workflow execution instance for one business record.
**DFR**: `DFR-04-001`, `DFR-04-011`, `DFR-04-013`, `DFR-04-014`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | — | — | — | Yes | `Name` | — | `compute='_compute_name'`, `store=True` |
| `definition_id` | `Many2one('workflow.definition')` | Yes | — | Yes | Yes | `Definition` | — | `ondelete='restrict'` |
| `definition_version_id` | `Many2one('workflow.definition.version')` | Yes | — | Yes | Yes | `Version` | — | `ondelete='restrict'`; pinned at start (`DFR-01-010`) |
| `state` | `Selection` | Yes | `running` | Yes | — | `State` | — | See state machine below |
| `res_model` | `Char(128)` | Yes | — | Yes | Yes | `Resource Model` | — | — |
| `res_id` | `Many2oneReference` | Yes | — | Yes | Yes | `Resource ID` | — | `model_field='res_model'` |
| `started_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Started At` | — | — |
| `ended_at_utc` | `Datetime` | No | — | — | Yes | `Ended At` | — | Set on terminal state |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | Yes | `Company` | — | — |
| `requester_id` | `Many2one('res.users')` | Yes | `lambda self: self.env.user` | Yes | Yes | `Requester` | — | `ondelete='restrict'` |
| `correlation_id` | `Char(64)` | No | — | Yes | Yes | `Correlation ID` | — | Generated at start if blank |
| `active` | `Boolean` | — | `True` | — | — | `Active` | — | Used for archival |
| `task_ids` | `One2many('workflow.task', 'instance_id')` | — | — | — | Yes | `Tasks` | — | — |
| `token_ids` | `One2many('workflow.token', 'instance_id')` | — | — | — | Yes | `Tokens` | — | — |
| `decision_event_ids` | `One2many('workflow.decision.event', 'instance_id')` | — | — | — | Yes | `Decision Events` | — | — |
| `node_runtime_ids` | `One2many('workflow.node.runtime', 'instance_id')` | — | — | — | Yes | `Node Runtimes` | — | — |

**State Machine** (`state` selection values):

| Value | String | Terminal |
|---|---|---|
| `running` | `Running` | No |
| `waiting_human` | `Waiting (Human)` | No |
| `waiting_timer` | `Waiting (Timer)` | No |
| `completed_approved` | `Approved` | Yes |
| `completed_rejected` | `Rejected` | Yes |
| `cancelled` | `Cancelled` | Yes |
| `error_incident` | `Error` | No |

**State Transition Table:**

| From State | To State | Trigger | Guard | DFR |
|---|---|---|---|---|
| `running` | `waiting_human` | Human task node activated | Task created and assigned | `DFR-04-014` |
| `running` | `waiting_timer` | Timer event node activated | Timer boundary set | `DFR-04-014` |
| `running` | `completed_approved` | Final approval node reached | All required approvals collected | `DFR-04-013` |
| `running` | `completed_rejected` | Rejection at any step | Rejection is terminal | `DFR-04-013` |
| `running` | `cancelled` | `action_cancel()` by admin/requester | Instance not in terminal state | `DFR-02-006` |
| `running` | `error_incident` | Unhandled exception in `_tick()` | Exception logged as incident | `DFR-09-002` |
| `waiting_human` | `running` | Task decision received | Task completed, more nodes remain | `DFR-04-011` |
| `waiting_human` | `completed_approved` | Task approved at final step | No remaining nodes | `DFR-04-013` |
| `waiting_human` | `completed_rejected` | Task rejected | Rejection is terminal | `DFR-04-013` |
| `waiting_human` | `cancelled` | `action_cancel()` | Instance not in terminal state | `DFR-02-006` |
| `waiting_human` | `error_incident` | SLA/escalation failure | Incident created | `DFR-09-002` |
| `waiting_timer` | `running` | Timer fires | Timer duration elapsed | `DFR-04-014` |
| `waiting_timer` | `cancelled` | `action_cancel()` | Instance not in terminal state | `DFR-02-006` |
| `error_incident` | `running` | Incident resolved, orchestrator retries | Manual incident resolution | `DFR-09-004` |
| `error_incident` | `cancelled` | Incident escalated to cancellation | Admin decision | `DFR-09-002` |

**Precedence** (descending): `error_incident` → terminals → `running` → `waiting_human` → `waiting_timer`

**Invariants:** Terminal states (`completed_approved`, `completed_rejected`, `cancelled`) have no outbound transitions. `ended_at_utc` is set on any transition to a terminal state.

**Computed Methods**:

| Method | Dependencies | Logic |
|---|---|---|
| `_compute_name` | `definition_id.name`, `res_model`, `res_id` | `f"{definition.name} / {res_model},{res_id}"` |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_start` | `binding_context: dict` | `self` | `DFR-04-001` |
| `action_cancel` | `reason_code: str` | `self` | `DFR-02-006` |
| `_tick` | — | — | `DFR-04-011` |
| `_acquire_instance_lock` | — | `bool` | `DFR-04-011` |
| `_update_aggregate_state` | — | — | `DFR-04-014` |
| `_dispatch_post_commit` | `events: list` | — | SDS §6.2 |

---

## 9. `workflow.node.runtime`

**File**: `models/workflow_node_runtime.py`
**Description**: Runtime status per BPMN node per instance. New record per rework iteration.
**DFR**: `DFR-04-014`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `instance_id` | `Many2one('workflow.instance')` | Yes | — | Yes | Yes | `Instance` | — | `ondelete='cascade'` |
| `node_id` | `Char(64)` | Yes | — | Yes | Yes | `Node ID` | `BPMN element ID` | — |
| `node_type` | `Selection` | Yes | — | — | Yes | `Node Type` | — | `start_event`, `end_event`, `user_task`, `exclusive_gateway`, `parallel_gateway`, `timer_event` |
| `state` | `Selection` | Yes | `pending` | Yes | — | `State` | — | `pending`, `active`, `completed`, `timed_out`, `skipped` |
| `sequence` | `Integer` | — | `10` | — | — | `Sequence` | — | — |
| `loop_iteration` | `Integer` | — | `1` | — | Yes | `Loop Iteration` | `Rework loop counter` | Max configurable 1–99, default cap 5 |
| `activated_at_utc` | `Datetime` | No | — | — | Yes | `Activated At` | — | Set on `pending → active` |
| `completed_at_utc` | `Datetime` | No | — | Yes | Yes | `Completed At` | — | Set on terminal transition |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='instance_id.company_id'`, `store=True` |

**State Machine** (`state` selection values):

| Value | String | Terminal |
|---|---|---|
| `pending` | `Pending` | No |
| `active` | `Active` | No |
| `completed` | `Completed` | Yes |
| `timed_out` | `Timed Out` | Yes |
| `skipped` | `Skipped` | Yes |

---

## 10. `workflow.token`

**File**: `models/workflow_token.py`
**Description**: Branch progress marker. Tokens are never deleted — state transitions only.
**DFR**: `DFR-04-013`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `instance_id` | `Many2one('workflow.instance')` | Yes | — | Yes | Yes | `Instance` | — | `ondelete='cascade'` |
| `node_runtime_id` | `Many2one('workflow.node.runtime')` | No | — | Yes | — | `Current Node` | — | `ondelete='set null'`; updated on advance |
| `parent_token_id` | `Many2one('workflow.token')` | No | — | Yes | Yes | `Parent Token` | — | `ondelete='set null'`; set on parallel split |
| `branch_id` | `Char(64)` | No | — | Yes | Yes | `Branch ID` | — | Group identifier for join resolution |
| `state` | `Selection` | Yes | `active` | Yes | — | `State` | — | `active`, `consumed`, `cancelled` |
| `cancel_reason` | `Selection` | No | — | — | — | `Cancel Reason` | — | `branch_superseded`, `instance_cancelled`, `rework` |
| `created_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Created At` | — | — |
| `consumed_at_utc` | `Datetime` | No | — | — | Yes | `Consumed At` | — | Set on `active → consumed` |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='instance_id.company_id'`, `store=True` |

**CRUD Overrides**:

| Method | Reason |
|---|---|
| `unlink` | Blocked — tokens are never deleted |

---

## 11. `workflow.decision.event`

**File**: `models/workflow_decision_event.py`
**Description**: User or system decision input that may advance runtime.
**DFR**: `DFR-04-001`, `DFR-04-003`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `instance_id` | `Many2one('workflow.instance')` | Yes | — | Yes | Yes | `Instance` | — | `ondelete='cascade'` |
| `task_id` | `Many2one('workflow.task')` | No | — | Yes | Yes | `Task` | — | `ondelete='set null'` |
| `decision` | `Selection` | Yes | — | — | Yes | `Decision` | — | `approve`, `reject`, `request_change`, `delegate`, `escalate`, `auto_approve`, `auto_reject` |
| `actor_id` | `Many2one('res.users')` | Yes | — | Yes | Yes | `Actor` | — | `ondelete='restrict'` |
| `comment` | `Text` | No | — | — | — | `Comment` | — | — |
| `occurred_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Occurred At` | — | — |
| `idempotency_key` | `Char(128)` | No | — | Yes | Yes | `Idempotency Key` | — | — |
| `correlation_id` | `Char(64)` | No | — | Yes | Yes | `Correlation ID` | — | — |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='instance_id.company_id'`, `store=True` |

---

## 12. `workflow.task`

**File**: `models/workflow_task.py`
**Inherits**: `mail.thread`, `mail.activity.mixin`
**Description**: Human approval task with assignment, SLA, and decision metadata.
**DFR**: `DFR-05-009`, `DFR-05-010`, `DFR-05-011`, `DFR-05-014`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Task Name` | — | — |
| `instance_id` | `Many2one('workflow.instance')` | Yes | — | Yes | Yes | `Instance` | — | `ondelete='cascade'` |
| `node_runtime_id` | `Many2one('workflow.node.runtime')` | No | — | Yes | Yes | `Node Runtime` | — | `ondelete='set null'` |
| `status` | `Selection` | Yes | `pending` | Yes | — | `Status` | — | See state machine |
| `decision` | `Selection` | No | — | — | — | `Decision` | — | `approve`, `reject`, `request_change` |
| `assignee_user_id` | `Many2one('res.users')` | No | — | Yes | — | `Assignee` | — | `ondelete='set null'` |
| `assignee_group_id` | `Many2one('res.groups')` | No | — | — | — | `Assignee Group` | — | `ondelete='set null'` |
| `delegated_from_id` | `Many2one('res.users')` | No | — | — | Yes | `Delegated From` | — | `ondelete='set null'`; original assignee before delegation |
| `sla_due_at_utc` | `Datetime` | No | — | Yes | — | `SLA Due` | — | Calculated at task creation |
| `is_overdue` | `Boolean` | — | — | Yes | Yes | `Overdue` | — | `compute='_compute_is_overdue'`, `store=True` |
| `completed_at_utc` | `Datetime` | No | — | — | Yes | `Completed At` | — | Set on terminal status |
| `comment` | `Text` | No | — | — | — | `Comment` | — | — |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='instance_id.company_id'`, `store=True` |
| `transition_ids` | `One2many('workflow.task.transition', 'task_id')` | — | — | — | Yes | `Transitions` | — | — |

**State Machine** (`status` selection values):

| Value | String | Terminal |
|---|---|---|
| `pending` | `Pending` | No |
| `assigned` | `Assigned` | No |
| `completed` | `Completed` | Yes |
| `cancelled` | `Cancelled` | Yes |
| `escalated` | `Escalated` | No |

**Computed Methods**:

| Method | Dependencies | Logic |
|---|---|---|
| `_compute_is_overdue` | `sla_due_at_utc`, `status` | `True` if `sla_due_at_utc < now` and status not terminal |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_approve` | `comment=None` | `self` | `DFR-05-010` |
| `action_reject` | `comment=None` | `self` | `DFR-05-010` |
| `action_request_change` | `comment` | `self` | `DFR-05-010` |
| `action_delegate` | `delegate_user_id, reason` | `self` | `DFR-05-005` |
| `action_escalate` | — | `self` | `DFR-05-012` |
| `action_cancel` | `reason` | `self` | — |
| `action_batch_decide` | `task_ids, decision, payload` | Result dict | `DFR-05-016` |
| `_cron_check_sla` | — | — | `DFR-05-011` |
| `_cron_check_deadlines` | — | — | `DFR-04-009` |

---

## 13. `workflow.task.transition`

**File**: `models/workflow_task_transition.py`
**Description**: Immutable transition event stream for task status changes.
**DFR**: `DFR-05-014`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `task_id` | `Many2one('workflow.task')` | Yes | — | Yes | Yes | `Task` | — | `ondelete='cascade'` |
| `from_status` | `Char(32)` | Yes | — | — | Yes | `From Status` | — | — |
| `to_status` | `Char(32)` | Yes | — | — | Yes | `To Status` | — | — |
| `actor_id` | `Many2one('res.users')` | No | — | Yes | Yes | `Actor` | — | `ondelete='set null'` |
| `reason` | `Text` | No | — | — | Yes | `Reason` | — | — |
| `occurred_at_utc` | `Datetime` | — | `fields.Datetime.now` | Yes | Yes | `Occurred At` | — | — |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='task_id.company_id'`, `store=True` |

**CRUD Overrides**:

| Method | Reason |
|---|---|
| `write` | Blocked — transitions are immutable |
| `unlink` | Blocked — transitions are never deleted |

---

## 14. `workflow.approver.resolution`

**File**: `models/workflow_approver_resolution.py`
**Description**: Approver source rules per step/node in a definition version.
**DFR**: `DFR-05-001`, `DFR-05-002`, `DFR-05-003`, `DFR-05-004`, `DFR-05-006`, `DFR-05-007`, `DFR-05-008`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Rule Name` | — | — |
| `definition_version_id` | `Many2one('workflow.definition.version')` | Yes | — | Yes | — | `Version` | — | `ondelete='cascade'` |
| `node_id` | `Char(64)` | Yes | — | Yes | — | `Node ID` | `BPMN element ID` | — |
| `sequence` | `Integer` | — | `10` | — | — | `Sequence` | — | Evaluation order |
| `resolution_type` | `Selection` | Yes | — | — | — | `Type` | — | `user`, `group`, `role`, `hierarchy`, `field`, `delegate` |
| `user_ids` | `Many2many('res.users')` | Cond | — | — | — | `Named Users` | — | Required when `type=user` |
| `group_id` | `Many2one('res.groups')` | Cond | — | — | — | `Group` | — | `ondelete='restrict'`; required when `type=group` or `role` |
| `field_path` | `Char(255)` | Cond | — | — | — | `Field Path` | `Dot-separated path to user field` | Required when `type=field`; max 3 hops |
| `hierarchy_levels` | `Integer` | Cond | `1` | — | — | `Hierarchy Levels` | — | Required when `type=hierarchy`; range 1–5 |
| `quorum_mode` | `Selection` | — | `all` | — | — | `Join Mode` | — | `all`, `any`, `quorum` |
| `quorum_count` | `Integer` | Cond | — | — | — | `Quorum Count` | `Absolute count` | Required when `quorum_mode=quorum` |
| `quorum_percentage` | `Float` | Cond | — | — | — | `Quorum %` | `Percentage (0–100)` | Used with quorum count as floor |
| `anti_self_approval` | `Boolean` | — | `True` | — | — | `Anti Self-Approval` | — | `DFR-05-006` |
| `separation_of_duty_rule` | `Text` | No | — | — | — | `SoD Rule` | `JSON rule for prohibited combos` | `DFR-05-007` |
| `fallback_type` | `Selection` | No | — | — | — | `Fallback Source` | — | `fallback_group`, `fallback_hierarchy_level`, `fallback_named_users`, `fallback_escalation_target` |
| `fallback_group_id` | `Many2one('res.groups')` | Cond | — | — | — | `Fallback Group` | — | `ondelete='set null'`; required when `fallback_type=fallback_group` |
| `fallback_user_ids` | `Many2many('res.users', 'workflow_resolution_fallback_user_rel')` | Cond | — | — | — | `Fallback Users` | — | Required when `fallback_type=fallback_named_users` |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='definition_version_id.company_id'`, `store=True` |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `resolve_approvers` | `instance_id, context` | `res.users` recordset | `DFR-05-001..004` |
| `_apply_anti_self` | `approver_set, requester_id` | Filtered `res.users` | `DFR-05-006` |
| `_apply_sod` | `approver_set, prior_decisions` | Filtered `res.users` | `DFR-05-007` |
| `_evaluate_fallback` | `empty_set_context` | `res.users` recordset | `DFR-05-008` |

---

## 15. `workflow.delegation.record`

**File**: `models/workflow_delegation_record.py`
**Description**: Delegation validity window and actor traceability.
**DFR**: `DFR-05-005`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `delegator_id` | `Many2one('res.users')` | Yes | — | Yes | — | `Delegator` | — | `ondelete='cascade'` |
| `delegate_id` | `Many2one('res.users')` | Yes | — | Yes | — | `Delegate` | — | `ondelete='cascade'` |
| `valid_from` | `Datetime` | Yes | — | — | — | `Valid From` | — | — |
| `valid_to` | `Datetime` | Yes | — | — | — | `Valid To` | — | Must be > `valid_from`; cannot outlive delegator account |
| `is_active` | `Boolean` | — | — | — | Yes | `Active` | — | `compute='_compute_is_active'`, `store=True` |
| `definition_id` | `Many2one('workflow.definition')` | No | — | — | — | `Definition Scope` | `Limit delegation to this definition` | `ondelete='set null'`; optional scope limitation |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | — |

**Python Constraints**:

```python
@api.constrains('valid_from', 'valid_to')
def _check_validity_window(self):
    """valid_to must be > valid_from."""

@api.constrains('delegator_id', 'delegate_id')
def _check_not_self_delegation(self):
    """Delegator and delegate must differ."""
```

**Computed Methods**:

| Method | Dependencies | Logic |
|---|---|---|
| `_compute_is_active` | `valid_from`, `valid_to` | `valid_from <= now < valid_to` |

---

## 16. `workflow.follower.rule`

**File**: `models/workflow_follower_rule.py`
**Description**: Auto-follow policies at definition version level.
**DFR**: `DFR-05-015`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Rule Name` | — | — |
| `definition_version_id` | `Many2one('workflow.definition.version')` | Yes | — | Yes | — | `Version` | — | `ondelete='cascade'` |
| `sequence` | `Integer` | — | `10` | — | — | `Sequence` | — | — |
| `follower_type` | `Selection` | Yes | — | — | — | `Follower Type` | — | `requester`, `approver`, `group`, `field` |
| `group_id` | `Many2one('res.groups')` | Cond | — | — | — | `Group` | — | `ondelete='restrict'`; required when `type=group` |
| `field_path` | `Char(255)` | Cond | — | — | — | `Field Path` | — | Required when `type=field` |
| `completion_policy` | `Selection` | — | `retained` | — | — | `On Completion` | — | `retained`, `downgraded`, `removed` |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='definition_version_id.company_id'`, `store=True` |

---

## 17. `workflow.condition.rule`

**File**: `models/workflow_condition_rule.py`
**Description**: Guard condition on sequence flows between BPMN nodes.
**DFR**: `DFR-04-003`, `DFR-04-006`, `DFR-04-007`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Rule Name` | — | — |
| `definition_version_id` | `Many2one('workflow.definition.version')` | Yes | — | Yes | — | `Version` | — | `ondelete='cascade'` |
| `source_node_id` | `Char(64)` | Yes | — | Yes | — | `Source Node` | `BPMN element ID` | — |
| `target_node_id` | `Char(64)` | Yes | — | Yes | — | `Target Node` | `BPMN element ID` | — |
| `sequence` | `Integer` | — | `10` | — | — | `Sequence` | — | Evaluation priority |
| `condition_type` | `Selection` | Yes | `domain` | — | — | `Condition Type` | — | `domain`, `python` |
| `domain_filter` | `Text` | Cond | — | — | — | `Domain` | `JSON condition rule tree` | Required when `type=domain`; max 3 relational hops |
| `python_code` | `Text` | Cond | — | — | — | `Python Snippet` | — | Required when `type=python`; admin-only; sandboxed |
| `is_default` | `Boolean` | — | `False` | — | — | `Default Path` | — | At most one per gateway |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='definition_version_id.company_id'`, `store=True` |

**Python Constraints**:

```python
@api.constrains('condition_type', 'domain_filter', 'python_code')
def _check_condition_value(self):
    """domain_filter required for domain type; python_code required for python type."""
```

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `evaluate` | `record, context` | `bool` | `DFR-04-003` |
| `_evaluate_domain` | `record` | `bool` | `DFR-04-006` |
| `_evaluate_python` | `record, context` | `bool` | `DFR-04-007` |

---

## 18. `workflow.signature.evidence`

**File**: `models/workflow_signature_evidence.py`
**Description**: Immutable evidence record for human signature or system attestation.
**DFR**: `DFR-06-001`, `DFR-06-002`, `DFR-06-003`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `task_id` | `Many2one('workflow.task')` | Yes | — | Yes | Yes | `Task` | — | `ondelete='restrict'` |
| `instance_id` | `Many2one('workflow.instance')` | — | — | Yes | Yes | `Instance` | — | `related='task_id.instance_id'`, `store=True` |
| `signer_id` | `Many2one('res.users')` | Yes | — | Yes | Yes | `Signer` | — | `ondelete='restrict'` |
| `evidence_type` | `Selection` | Yes | — | — | Yes | `Evidence Type` | — | `human_signature`, `system_attestation` |
| `capture_method` | `Selection` | Yes | — | — | Yes | `Capture Method` | — | `click_to_sign`, `drawn_signature`, `otp_challenge`, `system_auto_attest` |
| `reason_code` | `Char(64)` | Yes | — | — | Yes | `Reason Code` | — | — |
| `evidence_hash` | `Char(64)` | Yes | — | — | Yes | `Evidence Hash` | `SHA-256 of artifact` | — |
| `evidence_ref` | `Char(255)` | Yes | — | — | Yes | `Evidence Reference` | `Pointer to stored artifact` | — |
| `attachment_id` | `Many2one('ir.attachment')` | No | — | — | Yes | `Attachment` | — | `ondelete='restrict'` |
| `policy_id` | `Many2one('workflow.attestation.policy')` | No | — | — | Yes | `Policy` | — | `ondelete='set null'` |
| `superseded_by_id` | `Many2one('workflow.signature.evidence')` | No | — | — | Yes | `Superseded By` | — | `ondelete='set null'` |
| `supersede_reason` | `Text` | Cond | — | — | Yes | `Supersede Reason` | — | Required when `superseded_by_id` set |
| `created_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Created At` | — | — |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='task_id.company_id'`, `store=True` |

**CRUD Overrides**:

| Method | Reason |
|---|---|
| `write` | Block all immutable fields (all except `superseded_by_id`, `supersede_reason`) |
| `unlink` | Blocked entirely |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `verify_integrity` | — | `bool` | `DFR-06-002` |
| `action_supersede` | `new_evidence_id, reason` | `self` | `DFR-06-003` |

---

## 19. `workflow.attestation.policy`

**File**: `models/workflow_attestation_policy.py`
**Description**: Step-level signature and attestation policy configuration.
**DFR**: `DFR-06-001`, `DFR-06-005`, `DFR-06-006`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Policy Name` | — | — |
| `definition_version_id` | `Many2one('workflow.definition.version')` | Yes | — | Yes | — | `Version` | — | `ondelete='cascade'` |
| `node_id` | `Char(64)` | Yes | — | Yes | — | `Node ID` | `BPMN element ID` | — |
| `signature_required` | `Boolean` | — | `False` | — | — | `Signature Required` | — | `DFR-06-001` |
| `legal_human_signature_required` | `Boolean` | — | `False` | — | — | `Legal Signature Required` | — | `DFR-06-006`; blocks timeout auto-approve |
| `allow_system_attestation_on_timeout` | `Boolean` | — | `False` | — | — | `Allow Attestation on Timeout` | — | `DFR-06-005`; ignored when legal sig required |
| `attestation_type` | `Selection` | No | — | — | — | `Attestation Type` | — | `human_signature`, `system_attestation` |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='definition_version_id.company_id'`, `store=True` |

**Python Constraints**:

```python
@api.constrains('legal_human_signature_required', 'allow_system_attestation_on_timeout')
def _check_legal_blocks_attestation(self):
    """legal_human_signature_required=True blocks allow_system_attestation_on_timeout."""
```

---

## 20. `workflow.access.grant`

**File**: `models/workflow_access_grant.py`
**Description**: Temporary least-privilege access grant for approvers.
**DFR**: `DFR-07-001`, `DFR-07-002`, `DFR-07-003`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `task_id` | `Many2one('workflow.task')` | Yes | — | Yes | Yes | `Task` | — | `ondelete='cascade'` |
| `instance_id` | `Many2one('workflow.instance')` | — | — | Yes | Yes | `Instance` | — | `related='task_id.instance_id'`, `store=True` |
| `user_id` | `Many2one('res.users')` | Yes | — | Yes | Yes | `User` | — | `ondelete='cascade'` |
| `res_model` | `Char(128)` | Yes | — | Yes | Yes | `Resource Model` | — | — |
| `res_id` | `Many2oneReference` | Yes | — | Yes | Yes | `Resource ID` | — | `model_field='res_model'` |
| `operation_set` | `Char(128)` | Yes | `read` | — | Yes | `Operations` | `Comma-separated: read,write` | — |
| `state` | `Selection` | Yes | `active` | Yes | — | `State` | — | `active`, `revoked`, `expired` |
| `expires_at_utc` | `Datetime` | Yes | — | Yes | — | `Expires At` | — | Min 5 min, max 72h from now; default +24h |
| `created_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Created At` | — | — |
| `revoked_at_utc` | `Datetime` | No | — | — | Yes | `Revoked At` | — | — |
| `revoke_reason` | `Selection` | No | — | — | — | `Revoke Reason` | — | `task_completed`, `task_reassigned`, `instance_cancelled`, `ttl_expired`, `manual` |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='instance_id.company_id'`, `store=True` |

**Python Constraints**:

```python
@api.constrains('expires_at_utc')
def _check_ttl_bounds(self):
    """TTL must be between 5 minutes and 72 hours from creation."""
```

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_revoke` | `reason` | `self` | `DFR-07-003` |
| `_cron_expire_grants` | — | — | `DFR-07-003` |
| `_cron_reconcile_orphan_grants` | — | — | SDS §11.2 |

---

## 21. `workflow.access.grant.log`

**File**: `models/workflow_access_grant_log.py`
**Description**: Immutable grant lifecycle event records.
**DFR**: `DFR-07-004`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `grant_id` | `Many2one('workflow.access.grant')` | Yes | — | Yes | Yes | `Grant` | — | `ondelete='cascade'` |
| `event_type` | `Selection` | Yes | — | — | Yes | `Event` | — | `created`, `revoked`, `expired`, `reconciled` |
| `actor_id` | `Many2one('res.users')` | No | — | — | Yes | `Actor` | — | — |
| `reason` | `Text` | No | — | — | Yes | `Reason` | — | — |
| `occurred_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Occurred At` | — | — |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='grant_id.company_id'`, `store=True` |

**CRUD Overrides**:

| Method | Reason |
|---|---|
| `write` | Blocked — immutable |
| `unlink` | Blocked — never deleted |

---

## 22. `workflow.notification.template`

**File**: `models/workflow_notification_template.py`
**Description**: Configurable notification templates per event type and channel.
**DFR**: `DFR-08-001`, `DFR-08-002`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Template Name` | — | — |
| `event_type` | `Selection` | Yes | — | Yes | — | `Event Type` | — | `task_assigned`, `task_reminder`, `task_escalated`, `task_completed`, `instance_approved`, `instance_rejected`, `sla_warning`, `sla_breached` |
| `channel` | `Selection` | Yes | `inbox` | — | — | `Channel` | — | `inbox`, `email` |
| `mail_template_id` | `Many2one('mail.template')` | Cond | — | — | — | `Mail Template` | — | `ondelete='restrict'`; required when `channel=email` |
| `is_active` | `Boolean` | — | `True` | — | — | `Active` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | — |

---

## 23. `workflow.notification.log`

**File**: `models/workflow_notification_log.py`
**Description**: Notification dispatch log for observability.
**DFR**: `DFR-08-001`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `instance_id` | `Many2one('workflow.instance')` | No | — | Yes | Yes | `Instance` | — | `ondelete='cascade'` |
| `task_id` | `Many2one('workflow.task')` | No | — | Yes | Yes | `Task` | — | `ondelete='set null'` |
| `template_id` | `Many2one('workflow.notification.template')` | No | — | — | Yes | `Template` | — | `ondelete='set null'` |
| `recipient_id` | `Many2one('res.users')` | No | — | Yes | Yes | `Recipient` | — | `ondelete='set null'` |
| `channel` | `Selection` | Yes | — | — | Yes | `Channel` | — | `inbox`, `email` |
| `state` | `Selection` | Yes | — | Yes | — | `State` | — | `sent`, `failed` |
| `error_message` | `Text` | No | — | — | — | `Error` | — | — |
| `sent_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Sent At` | — | — |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='instance_id.company_id'`, `store=True` |

---

## 24. `workflow.webhook.endpoint`

**File**: `models/workflow_webhook_endpoint.py`
**Description**: Outbound webhook endpoint configuration with HMAC secret.
**DFR**: `DFR-08-003`, `DFR-08-006`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | Yes | — | — | — | `Endpoint Name` | — | — |
| `url` | `Char(1024)` | Yes | — | — | — | `URL` | — | Must be HTTPS in production |
| `secret` | `Char(256)` | Yes | — | — | — | `HMAC Secret` | — | Used for HMAC-SHA256 signing |
| `secret_rotation_key` | `Char(256)` | No | — | — | — | `Rotation Key` | `Secondary key during rotation` | Dual validation; overlap 1–24h |
| `event_types` | `Char(512)` | No | — | — | — | `Event Types` | `Comma-separated filter` | — |
| `is_active` | `Boolean` | — | `True` | — | — | `Active` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | — |

---

## 25. `workflow.outbound.event`

**File**: `models/workflow_outbound_event.py`
**Description**: Outbound event model for webhook dispatch with retry and dead-letter.
**DFR**: `DFR-08-003`, `DFR-08-004`, `DFR-08-005`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `event_type` | `Char(64)` | Yes | — | Yes | Yes | `Event Type` | — | — |
| `schema_version` | `Char(16)` | — | `1.0` | — | Yes | `Schema Version` | — | — |
| `payload` | `Text` | Yes | — | — | Yes | `Payload` | `JSON canonical payload` | RFC-8785 canonical JSON |
| `payload_hash` | `Char(64)` | Yes | — | — | Yes | `Payload Hash` | `SHA-256` | — |
| `signature` | `Char(128)` | No | — | — | Yes | `HMAC Signature` | — | HMAC-SHA256 |
| `endpoint_id` | `Many2one('workflow.webhook.endpoint')` | Yes | — | Yes | Yes | `Endpoint` | — | `ondelete='restrict'` |
| `instance_id` | `Many2one('workflow.instance')` | No | — | Yes | Yes | `Instance` | — | `ondelete='set null'` |
| `state` | `Selection` | Yes | `pending` | Yes | — | `State` | — | `pending`, `delivered`, `failed`, `dead_letter` |
| `attempt_count` | `Integer` | — | `0` | — | — | `Attempts` | — | Max 5 |
| `max_attempts` | `Integer` | — | `5` | — | — | `Max Attempts` | — | — |
| `next_retry_at_utc` | `Datetime` | No | — | Yes | — | `Next Retry` | — | — |
| `last_error` | `Text` | No | — | — | — | `Last Error` | — | — |
| `last_http_status` | `Integer` | No | — | — | — | `HTTP Status` | — | — |
| `created_at_utc` | `Datetime` | — | `fields.Datetime.now` | Yes | Yes | `Created At` | — | — |
| `delivered_at_utc` | `Datetime` | No | — | — | Yes | `Delivered At` | — | — |
| `idempotency_key` | `Char(128)` | No | — | Yes | Yes | `Idempotency Key` | — | — |
| `correlation_id` | `Char(64)` | No | — | Yes | Yes | `Correlation ID` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | Yes | `Company` | — | — |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_dispatch` | — | `self` | `DFR-08-004` |
| `action_retry` | — | `self` | `DFR-08-004` |
| `action_dead_letter` | `reason` | `self` | `DFR-08-004` |
| `action_replay` | `actor` | `self` | `DFR-08-005` |
| `_compute_signature` | `secret` | `str` | `DFR-08-006` |
| `_compute_backoff` | — | `datetime` | SDS §6.7 |

---

## 26. `workflow.idempotency.registry`

**File**: `models/workflow_idempotency_registry.py`
**Description**: Dedicated idempotency check registry keyed by operation scope hash.
**DFR**: `DFR-10-001`, `DFR-10-002`, `DFR-10-003`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `operation_type` | `Selection` | Yes | — | — | Yes | `Operation Type` | — | `start`, `signal`, `complete_task`, `cancel_instance`, `reassign_task`, `execute_callback` |
| `operation_subject_ref` | `Char(255)` | Yes | — | — | Yes | `Subject Ref` | `e.g. workflow.instance,42` | — |
| `idempotency_key` | `Char(128)` | Yes | — | Yes | Yes | `Idempotency Key` | — | — |
| `operation_scope_hash` | `Char(64)` | Yes | — | `UNIQUE` | Yes | `Scope Hash` | `SHA-256 of (type, subject, key)` | — |
| `payload_hash` | `Char(64)` | Yes | — | — | Yes | `Payload Hash` | `SHA-256 of canonical request` | — |
| `result_status` | `Selection` | No | — | — | — | `Result` | — | `success`, `conflict`, `error` |
| `result_ref` | `Char(255)` | No | — | — | — | `Result Ref` | — | — |
| `correlation_id` | `Char(64)` | No | — | Yes | Yes | `Correlation ID` | — | — |
| `causation_id` | `Char(64)` | No | — | — | Yes | `Causation ID` | — | — |
| `created_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Created At` | — | — |
| `expires_at_utc` | `Datetime` | No | — | Yes | — | `Expires At` | — | Default: +90 days (configurable via `ir.config_parameter`) |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | Yes | `Company` | — | — |

**SQL Constraints**:

```python
_unique_scope_hash = models.Constraint(
    'UNIQUE(operation_scope_hash)',
    'Operation scope hash must be unique (at-most-once).',
)
```

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `check_or_register` | `operation_type, subject_ref, key, payload_hash` | `(is_new, result_ref)` | `DFR-10-001` |
| `_compute_scope_hash` | `operation_type, subject_ref, key` | `str` | `DFR-10-001` |
| `_cron_purge_expired` | — | — | SDS §10.5 |

---

## 27. `workflow.incident`

**File**: `models/workflow_incident.py`
**Inherits**: `mail.thread`
**Description**: Incident queue with controlled recovery actions.
**DFR**: `DFR-02-014`, `DFR-04-008`, `DFR-09-002`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(128)` | — | — | — | Yes | `Name` | — | `compute='_compute_name'`, `store=True` |
| `instance_id` | `Many2one('workflow.instance')` | No | — | Yes | Yes | `Instance` | — | — |
| `category` | `Selection` | Yes | — | Yes | Yes | `Category` | — | `callback_failure`, `resolution_failure`, `enforcement_failure`, `timer_failure`, `integrity_failure`, `webhook_failure` |
| `severity` | `Selection` | Yes | — | Yes | — | `Severity` | — | `low`, `medium`, `high`, `critical` |
| `state` | `Selection` | Yes | `open` | Yes | — | `State` | — | `open`, `triaged`, `retry_scheduled`, `resolved`, `closed_with_exception` |
| `reason_code` | `Char(64)` | No | — | — | Yes | `Reason Code` | — | — |
| `description` | `Text` | No | — | — | — | `Description` | — | — |
| `resolution_action` | `Selection` | No | — | — | — | `Resolution Action` | — | `retry`, `manual_resolution_link`, `close_with_exception` |
| `resolution_note` | `Text` | No | — | — | — | `Resolution Note` | — | — |
| `opened_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Opened At` | — | — |
| `resolved_at_utc` | `Datetime` | No | — | — | Yes | `Resolved At` | — | — |
| `correlation_id` | `Char(64)` | No | — | Yes | Yes | `Correlation ID` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | — |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `action_triage` | — | `self` | `DFR-09-002` |
| `action_retry` | — | `self` | `DFR-09-002` |
| `action_resolve` | `note` | `self` | `DFR-09-002` |
| `action_close_with_exception` | `note` | `self` | `DFR-09-002` |

---

## 28. `workflow.audit.event`

**File**: `models/workflow_audit_event.py`
**Description**: Immutable, append-only audit event timeline.
**DFR**: `DFR-07-007`, `DFR-07-010`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `event_type` | `Char(128)` | Yes | — | Yes | Yes | `Event Type` | — | e.g. `workflow.definition.published` |
| `actor_id` | `Many2one('res.users')` | No | — | Yes | Yes | `Actor` | — | — |
| `occurred_at_utc` | `Datetime` | — | `fields.Datetime.now` | Yes | Yes | `Occurred At` | — | — |
| `object_ref` | `Char(255)` | Yes | — | Yes | Yes | `Object Reference` | `model,id format` | — |
| `payload_hash` | `Char(64)` | No | — | — | Yes | `Payload Hash` | `SHA-256` | — |
| `payload` | `Text` | No | — | — | Yes | `Payload` | `JSON event payload` | — |
| `correlation_id` | `Char(64)` | No | — | Yes | Yes | `Correlation ID` | — | — |
| `causation_id` | `Char(64)` | No | — | — | Yes | `Causation ID` | — | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | Yes | `Company` | — | — |

**CRUD Overrides**:

| Method | Reason |
|---|---|
| `write` | Blocked — events are immutable |
| `unlink` | Blocked — events are never deleted |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `log_event` | `event_type, object_ref, payload=None, correlation_id=None, causation_id=None` | Record | `DFR-07-007` |

---

## 29. `workflow.approval.mixin`

**File**: `models/workflow_approval_mixin.py`
**Description**: Abstract mixin for business models to integrate with workflow system.
**No database table** — `_auto = False`.

```python
_name = 'workflow.approval.mixin'
_description = 'Workflow Approval Mixin'
```

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `workflow_instance_ids` | `One2many('workflow.instance', compute='_compute_workflow_instance_ids')` | — | — | — | Yes | `Workflow Instances` | — | Domain-filtered by `res_model` + `res_id` |
| `workflow_state` | `Selection` | — | — | — | Yes | `Workflow State` | — | `none`, `pending`, `approved`, `rejected`; `compute='_compute_workflow_state'` |

**Computed Methods**:

| Method | Dependencies | Logic |
|---|---|---|
| `_compute_workflow_instance_ids` | — | Search `workflow.instance` where `res_model=self._name, res_id=self.id` |
| `_compute_workflow_state` | `workflow_instance_ids` | Aggregate: any `running/waiting_*` → `pending`; all `approved` → `approved`; any `rejected` → `rejected`; else `none` |

---

## 30. `workflow.definition.tag`

**File**: `models/workflow_definition.py` (same file as `workflow.definition`)
**Description**: Categorization tags for workflow definitions.

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `name` | `Char(64)` | Yes | — | — | — | `Tag Name` | — | — |
| `color` | `Integer` | — | `0` | — | — | `Color` | `Kanban color index (0–11)` | — |
| `company_id` | `Many2one('res.company')` | Yes | `lambda self: self.env.company` | Yes | — | `Company` | — | `ondelete='cascade'` |

**SQL Constraints**:

```python
_unique_name_company = models.Constraint(
    'UNIQUE(name, company_id)',
    'Tag name must be unique per company.',
)
```

> **Convention note (GAP-01-06):** All `_hash` fields across the OMB use SHA-256 (hex-encoded, lowercase, 64 chars). This applies to `bpmn_hash`, `evidence_hash`, `payload_hash`, `operation_scope_hash`.

---

## Cross-Reference: Model → File Map

| # | Model `_name` | Python File | Inherits | Table |
|---|---|---|---|---|
| 1 | `workflow.definition` | `workflow_definition.py` | `mail.thread`, `mail.activity.mixin` | Yes |
| 2 | `workflow.definition.tag` | `workflow_definition.py` | — | Yes |
| 3 | `workflow.definition.version` | `workflow_definition_version.py` | `mail.thread` | Yes |
| 4 | `workflow.definition.compiled` | `workflow_definition_compiled.py` | — | Yes |
| 5 | `workflow.binding` | `workflow_binding.py` | `mail.thread` | Yes |
| 6 | `workflow.binding.scope` | `workflow_binding_scope.py` | — | Yes |
| 7 | `workflow.enforcement.interceptor` | `workflow_enforcement_interceptor.py` | — | No (abstract) |
| 8 | `workflow.instance` | `workflow_instance.py` | `mail.thread` | Yes |
| 9 | `workflow.node.runtime` | `workflow_node_runtime.py` | — | Yes |
| 10 | `workflow.token` | `workflow_token.py` | — | Yes |
| 11 | `workflow.decision.event` | `workflow_decision_event.py` | — | Yes |
| 12 | `workflow.task` | `workflow_task.py` | `mail.thread`, `mail.activity.mixin` | Yes |
| 13 | `workflow.task.transition` | `workflow_task_transition.py` | — | Yes |
| 14 | `workflow.approver.resolution` | `workflow_approver_resolution.py` | — | Yes |
| 15 | `workflow.delegation.record` | `workflow_delegation_record.py` | — | Yes |
| 16 | `workflow.follower.rule` | `workflow_follower_rule.py` | — | Yes |
| 17 | `workflow.condition.rule` | `workflow_condition_rule.py` | — | Yes |
| 18 | `workflow.signature.evidence` | `workflow_signature_evidence.py` | — | Yes |
| 19 | `workflow.attestation.policy` | `workflow_attestation_policy.py` | — | Yes |
| 20 | `workflow.access.grant` | `workflow_access_grant.py` | — | Yes |
| 21 | `workflow.access.grant.log` | `workflow_access_grant_log.py` | — | Yes |
| 22 | `workflow.notification.template` | `workflow_notification_template.py` | — | Yes |
| 23 | `workflow.notification.log` | `workflow_notification_log.py` | — | Yes |
| 24 | `workflow.webhook.endpoint` | `workflow_webhook_endpoint.py` | — | Yes |
| 25 | `workflow.outbound.event` | `workflow_outbound_event.py` | — | Yes |
| 26 | `workflow.idempotency.registry` | `workflow_idempotency_registry.py` | — | Yes |
| 27 | `workflow.incident` | `workflow_incident.py` | `mail.thread` | Yes |
| 28 | `workflow.audit.event` | `workflow_audit_event.py` | — | Yes |
| 29 | `workflow.approval.mixin` | `workflow_approval_mixin.py` | — | No (abstract) |
