# Code Generation Instructions — Dynamic Approval Workflow

> Read by Copilot when generating code inline and in chat.
> Supplements `copilot-instructions.md` with concrete generation patterns.

## Model Template

When asked to create a new workflow model, use this skeleton:

```python
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WorkflowModelName(models.Model):
    _name = 'workflow.model.name'
    _description = 'Workflow Model Name'
    _order = 'create_date desc'

    # -- Relational fields --
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # -- Stored fields --
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    state = fields.Selection(
        selection=[],
        default='draft',
        required=True,
        index=True,
    )

    # -- Computed fields --

    # -- Compute methods --

    # -- Constraints --

    # -- CRUD overrides --

    # -- Action methods --

    # -- Business methods --
```

## Security CSV Row Template

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_workflow_model_name_approver,workflow.model.name approver,model_workflow_model_name,dynamic_approval_core.group_workflow_approver,1,0,0,0
access_workflow_model_name_designer,workflow.model.name designer,model_workflow_model_name,dynamic_approval_core.group_workflow_designer,1,1,1,0
access_workflow_model_name_admin,workflow.model.name admin,model_workflow_model_name,dynamic_approval_core.group_workflow_admin,1,1,1,1
access_workflow_model_name_auditor,workflow.model.name auditor,model_workflow_model_name,dynamic_approval_core.group_workflow_auditor,1,0,0,0
```

## Record Rule Template

```xml
<record id="rule_workflow_model_name_company" model="ir.rule">
    <field name="name">Workflow Model Name: Company Isolation</field>
    <field name="model_id" ref="model_workflow_model_name"/>
    <field name="global" eval="True"/>
    <field name="domain_force">
        ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
    </field>
</record>
```

## Test Template

```python
from odoo.tests import tagged, TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestWorkflowFeature(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        # Create test data here

    def test_positive_scenario_succeeds(self):
        """Validates FR-XXX: description of requirement."""
        # Arrange
        # Act
        # Assert with message
        self.assertEqual(result, expected, "Expected X because Y")

    def test_negative_scenario_raises(self):
        """Validates FR-XXX: description of guard condition."""
        with self.assertRaises(UserError, msg="Should block because Y"):
            # Act
```

## Cron Template

```xml
<record id="ir_cron_workflow_action_name" model="ir.cron">
    <field name="name">DAW: Action Description</field>
    <field name="model_id" ref="model_workflow_model_name"/>
    <field name="state">code</field>
    <field name="code">model._cron_action_name()</field>
    <field name="interval_number">5</field>
    <field name="interval_type">minutes</field>
    <field name="active" eval="True"/>
    <field name="numbercall">-1</field>
</record>
```

## queue_job Pattern

```python
def _do_something(self):
    """Synchronous logic within transaction."""
    # ... business logic ...

    # Post-commit: enqueue async work
    self.env.cr.postcommit.add(
        lambda: self.with_delay(
            max_retries=3,
            retry_pattern={1: 5, 2: 30, 3: 120},
        )._job_async_work(record_id)
    )

def _job_async_work(self, record_id):
    """Async job executed by queue_job worker.

    Retry policy: 3 retries with 5s/30s/120s backoff.
    On exhaustion: creates workflow.incident.
    """
    record = self.browse(record_id).exists()
    if not record:
        return  # Record deleted between enqueue and execution
    # ... async work ...
```

## OWL Component Pattern

```javascript
/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class DawComponentName extends Component {
    static template = "dynamic_approval_bpmn.DawComponentName";
    static props = {
        recordId: { type: Number },
    };

    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");

        onWillStart(async () => {
            // Load lazy assets here
        });

        onMounted(() => {
            // DOM ready
        });

        onWillUnmount(() => {
            // Cleanup
        });
    }
}
```

## Immutable Model Pattern

For models that must enforce immutability (evidence, audit events):

```python
def write(self, vals):
    allowed = {'superseded_by', 'superseded_reason'}
    immutable = set(vals.keys()) - allowed
    if immutable:
        raise UserError(
            _("%(model)s records are immutable. Cannot modify: %(fields)s",
              model=self._description,
              fields=', '.join(sorted(immutable)))
        )
    return super().write(vals)

def unlink(self):
    raise UserError(
        _("%(model)s records cannot be deleted.", model=self._description)
    )
```

## Advisory Lock Pattern

```python
def _acquire_instance_lock(self, instance_id):
    """Acquire per-instance advisory lock within current transaction.

    # ADR-004: lock scoped to transaction, released on commit/rollback.
    """
    timeout_ms = int(self.env['ir.config_parameter'].sudo().get_param(
        'daw.lock_timeout_ms', '10000'
    ))
    self.env.cr.execute("SET LOCAL lock_timeout = %s", [timeout_ms])
    lock_key = hash(('workflow.instance', instance_id)) & 0x7FFFFFFFFFFFFFFF
    try:
        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(%s)", [lock_key]
        )
    except Exception:
        raise WorkflowLockTimeoutError(
            _("Could not acquire lock for workflow instance %s", instance_id)
        )
```

## Exception Pattern

```python
from odoo.exceptions import UserError


class WorkflowError(UserError):
    """Base exception for all workflow errors."""


class WorkflowGateBlockedError(WorkflowError):
    """Action blocked by workflow gate."""


class WorkflowLockTimeoutError(WorkflowError):
    """Per-instance lock acquisition timeout."""
```

## Field Naming Conventions

| Pattern | Example | When to use |
|---|---|---|
| `*_id` | `instance_id` | Many2one relational |
| `*_ids` | `task_ids` | One2many / Many2many |
| `*_count` | `task_count` | Integer compute for stat button |
| `*_at` / `*_at_utc` | `started_at_utc` | Datetime timestamps |
| `*_ref` | `result_ref` | Char reference to external record |
| `*_hash` | `payload_hash` | SHA-256 digest string |
| `is_*` | `is_active` | Boolean flags |
| `has_*` | `has_signature` | Boolean computed existence check |
