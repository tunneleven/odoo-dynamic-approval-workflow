import hashlib
import json
import time
import uuid
from json import JSONDecodeError

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

from ..exceptions import WorkflowConfigurationError, WorkflowLockTimeoutError, WorkflowRuntimeError


class WorkflowInstance(models.Model):
    """Runtime workflow execution for a single business record.

    States follow SDS §6.5 / SRS-04 §5.2 operational semantics:
    ``running``, ``waiting_human``, ``waiting_timer``,
    ``completed_approved``, ``completed_rejected``, ``cancelled``,
    ``error_incident``.

    SRS: FR-021..FR-028  |  DFR: DFR-04-001..DFR-04-014
    """

    _name = "workflow.instance"
    _description = "Workflow Instance"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    _terminal_states = frozenset({"completed_approved", "completed_rejected", "cancelled"})
    _wait_state_by_node_type = {
        "user_task": "waiting_human",
        "timer_event": "waiting_timer",
    }
    _allowed_state_transitions = {
        "running": frozenset(
            {
                "waiting_human",
                "waiting_timer",
                "completed_approved",
                "completed_rejected",
                "cancelled",
                "error_incident",
            }
        ),
        "waiting_human": frozenset(
            {"running", "completed_approved", "completed_rejected", "cancelled", "error_incident"}
        ),
        "waiting_timer": frozenset({"running", "cancelled"}),
        "error_incident": frozenset({"running", "cancelled"}),
    }

    definition_id = fields.Many2one(
        "workflow.definition",
        required=True,
        ondelete="restrict",
        index=True,
        readonly=True,
    )
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="restrict",
        index=True,
        readonly=True,
        help="Pinned at start time - never changes during execution.",
    )
    res_id = fields.Many2oneReference(
        string="Resource ID",
        model_field="res_model",
        required=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        readonly=True,
    )
    requester_id = fields.Many2one(
        "res.users",
        string="Requester",
        required=True,
        default=lambda self: self.env.user,
        index=True,
        readonly=True,
    )
    task_ids = fields.One2many(
        "workflow.task",
        "instance_id",
        string="Tasks",
        readonly=True,
    )
    token_ids = fields.One2many(
        "workflow.token",
        "instance_id",
        string="Tokens",
        readonly=True,
    )
    decision_event_ids = fields.One2many(
        "workflow.decision.event",
        "instance_id",
        string="Decision Events",
        readonly=True,
    )
    node_runtime_ids = fields.One2many(
        "workflow.node.runtime",
        "instance_id",
        string="Node Runtimes",
        readonly=True,
    )
    state = fields.Selection(
        [
            ("running", "Running"),
            ("waiting_human", "Waiting - Human"),
            ("waiting_timer", "Waiting - Timer"),
            ("completed_approved", "Approved"),
            ("completed_rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("error_incident", "Error / Incident"),
        ],
        default="running",
        required=True,
        tracking=True,
        index=True,
    )
    res_model = fields.Char(
        string="Resource Model",
        required=True,
        index=True,
        readonly=True,
    )
    started_at_utc = fields.Datetime(
        string="Started At (UTC)",
        default=fields.Datetime.now,
        readonly=True,
    )
    ended_at_utc = fields.Datetime(
        string="Ended At (UTC)",
        readonly=True,
    )
    correlation_id = fields.Char(
        size=64,
        index=True,
        readonly=True,
        help="End-to-end trace identifier.",
    )
    active = fields.Boolean(default=True)
    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=True,
    )

    @api.depends("definition_id.name", "res_model", "res_id")
    def _compute_name(self):
        """Compute the display label from definition and target reference."""
        for record in self:
            definition_name = record.definition_id.name or ""
            target_reference = "%s,%s" % (record.res_model or "", record.res_id or "")
            record.name = "%s / %s" % (definition_name, target_reference)

    def _runtime_actor_id(self):
        """Return the original actor ID for internal runtime side effects."""
        self.ensure_one()
        actor_id = self.env.context.get("workflow_actor_id")
        if actor_id and self.env.is_superuser():
            return actor_id
        return self.env.user.id

    def _get_runtime_actor_user(self):
        """Return the effective actor user for runtime authorization checks."""
        self.ensure_one()
        actor = self.env["res.users"].browse(self._runtime_actor_id()).exists()
        if not actor:
            raise AccessError(_("Workflow runtime actor is invalid."))
        return actor

    def _runtime_admin_self(self, **context_updates):
        """Return the instance with internal elevation for runtime persistence."""
        self.ensure_one()
        runtime_context = dict(self.env.context, workflow_actor_id=self._runtime_actor_id())
        runtime_context.update(context_updates)
        return self.with_context(runtime_context).sudo()

    def _check_start_authorization(self):
        """Ensure the runtime start actor is authorized."""
        self.ensure_one()
        actor = self._get_runtime_actor_user()
        if actor == self.requester_id or actor.has_group("dynamic_approval_core.group_workflow_admin"):
            return
        raise AccessError(_("Only the requester or a workflow admin can start this workflow instance."))

    def _check_cancel_authorization(self):
        """Ensure the cancel actor is authorized."""
        self.ensure_one()
        actor = self._get_runtime_actor_user()
        if self.state == "error_incident":
            if actor.has_group("dynamic_approval_core.group_workflow_admin"):
                return
            raise AccessError(_("Only a workflow admin can cancel an incidented workflow instance."))
        if actor == self.requester_id or actor.has_group("dynamic_approval_core.group_workflow_admin"):
            return
        raise AccessError(_("Only the requester or a workflow admin can cancel this workflow instance."))

    def _check_recover_authorization(self):
        """Ensure the recover actor is authorized."""
        self.ensure_one()
        actor = self._get_runtime_actor_user()
        if actor.has_group("dynamic_approval_core.group_workflow_admin"):
            return
        raise AccessError(_("Only a workflow admin can recover this workflow instance."))

    def action_start(self, binding_context):
        """Start runtime execution for the pinned workflow version."""
        self.ensure_one()
        if not isinstance(binding_context, dict):
            raise WorkflowConfigurationError(_("Binding context must be a dictionary."))

        runtime_self = self._runtime_admin_self(workflow_binding_context=dict(binding_context))
        runtime_self._check_start_authorization()
        runtime_self._acquire_instance_lock()
        runtime_self.invalidate_recordset()
        runtime_self._validate_start_conditions()
        start_node_spec = runtime_self._get_start_node_spec(runtime_self._get_compiled_artifact())

        runtime_self.write(
            {
                "correlation_id": runtime_self.correlation_id or uuid.uuid4().hex,
                "started_at_utc": runtime_self.started_at_utc or fields.Datetime.now(),
            }
        )
        start_node_runtime = runtime_self._create_node_runtime(start_node_spec)
        runtime_self.env["workflow.token"].create(
            {
                "instance_id": runtime_self.id,
                "node_runtime_id": start_node_runtime.id,
            }
        )
        runtime_self._dispatch_post_commit(
            [{"event_type": "workflow.instance.started", "instance_id": runtime_self.id}]
        )
        runtime_self._tick()
        self.invalidate_recordset()
        return self

    def action_cancel(self, reason_code):
        """Cancel the runtime instance and close all active runtime records."""
        self.ensure_one()
        if not reason_code:
            raise WorkflowRuntimeError(_("Cancellation reason code is required."))
        runtime_self = self._runtime_admin_self()
        runtime_self._acquire_instance_lock()
        runtime_self.invalidate_recordset()
        runtime_self._check_cancel_authorization()
        if runtime_self.state in self._terminal_states:
            raise WorkflowRuntimeError(_("Terminal workflow instances cannot be cancelled again."))

        runtime_self._cancel_active_runtime_records()
        runtime_self._transition_state("cancelled")
        runtime_self._dispatch_post_commit(
            [{"event_type": "workflow.instance.cancelled", "instance_id": runtime_self.id, "reason_code": reason_code}]
        )
        self.invalidate_recordset()
        return self

    def action_recover(self):
        """Recover an incidented instance after blocking incidents are resolved."""
        self.ensure_one()
        runtime_self = self._runtime_admin_self()
        runtime_self._check_recover_authorization()
        runtime_self._acquire_instance_lock()
        runtime_self.invalidate_recordset()
        if runtime_self.state != "error_incident":
            raise WorkflowRuntimeError(_("Only incidented workflow instances can be recovered."))
        if runtime_self._has_blocking_incident():
            raise WorkflowRuntimeError(_("Resolve all blocking incidents before recovering the workflow instance."))

        runtime_self._transition_state("running")
        runtime_self._tick()
        self.invalidate_recordset()
        return self

    def _tick(self):
        """Run one deterministic runtime tick against persisted state."""
        self.ensure_one()
        runtime_self = self._runtime_admin_self()
        if runtime_self.state in runtime_self._terminal_states:
            self.invalidate_recordset()
            return self

        runtime_self._acquire_instance_lock()
        runtime_self.invalidate_recordset()
        if runtime_self.state in {"waiting_human", "waiting_timer"}:
            runtime_self._transition_state("running")

        runtime_artifact = runtime_self._get_compiled_artifact()
        target_record = runtime_self._get_target_record()
        binding_context = dict(runtime_self.env.context.get("workflow_binding_context") or {})

        try:
            with runtime_self.env.cr.savepoint():
                runtime_self._run_runtime_loop(runtime_artifact, target_record, binding_context)
            runtime_self._update_aggregate_state(runtime_artifact=runtime_artifact)
        except Exception as err:
            runtime_self._handle_tick_failure(err)
        self.invalidate_recordset()
        return self

    def _evaluate_gate_condition(self, path_spec, target_record, binding_context):
        """Evaluate compiled route conditions via ``workflow.condition.rule`` helpers."""
        self.ensure_one()
        condition_values = dict(path_spec.get("condition_values") or {})
        if not condition_values:
            if path_spec.get("condition_rule_id"):
                raise WorkflowConfigurationError(
                    _("Compiled workflow route references missing condition metadata for rule '%s'.")
                    % path_spec["condition_rule_id"]
                )
            return None

        evaluation_context = {
            "binding_context": dict(binding_context or {}),
            "instance_id": self.id,
            "correlation_id": self.correlation_id,
        }
        rule_record = self.env["workflow.condition.rule"].new(
            {
                "name": condition_values.get("name") or path_spec["target_node_id"],
                "definition_version_id": self.definition_version_id.id,
                "source_node_id": path_spec.get("source_node_id") or False,
                "target_node_id": path_spec["target_node_id"],
                "condition_type": condition_values.get("condition_type") or "domain",
                "domain_filter": condition_values.get("domain_filter"),
                "python_code": condition_values.get("python_code"),
                "is_default": bool(condition_values.get("is_default")),
            }
        )
        try:
            return bool(rule_record.evaluate(target_record, evaluation_context))
        except Exception:
            return False

    def _dispatch_post_commit(self, events):
        """Persist workflow lifecycle events for downstream dispatching."""
        self.ensure_one()
        queued_events = [dict(event) for event in (events or []) if event]
        if not queued_events:
            return []

        audit_event_model = self.env["workflow.audit.event"].sudo()
        actor_id = self._runtime_actor_id()
        for event in queued_events:
            payload = dict(event)
            event_type = payload.pop("event_type")
            payload_str = json.dumps(payload, sort_keys=True, default=str) if payload else False
            payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest() if payload_str else False
            audit_event_model.create(
                {
                    "event_type": event_type,
                    "actor_id": actor_id,
                    "object_ref": payload.get("object_ref") or "workflow.instance,%s" % self.id,
                    "payload": payload_str,
                    "payload_hash": payload_hash,
                    "correlation_id": self.correlation_id,
                    "company_id": self.company_id.id,
                }
            )
        return queued_events

    def _update_aggregate_state(self, runtime_artifact=None):
        """Recompute the aggregate instance state from child runtime records."""
        self.ensure_one()
        if self.state in self._terminal_states:
            if not self.ended_at_utc:
                self.write({"ended_at_utc": fields.Datetime.now()})
            return self.state

        if self._has_blocking_incident():
            target_state = "error_incident"
        elif self._has_open_human_task():
            target_state = "waiting_human"
        elif self._has_active_timer_node():
            target_state = "waiting_timer"
        elif self._has_active_runtime():
            target_state = "running"
        else:
            target_state = self._derive_terminal_state(runtime_artifact=runtime_artifact) or "running"

        if target_state == "error_incident" and self.state == "waiting_timer":
            self._transition_state("running")
        self._transition_state(target_state)
        return self.state

    def _validate_start_conditions(self):
        """Validate that the instance can be started deterministically."""
        self.ensure_one()
        if self.state != "running":
            raise WorkflowRuntimeError(_("Workflow instances can only be started from the running state."))
        if self.token_ids or self.node_runtime_ids:
            raise WorkflowRuntimeError(_("Workflow instance has already been started."))
        if self.definition_version_id.definition_id != self.definition_id:
            raise WorkflowConfigurationError(_("Workflow definition version must belong to the selected definition."))
        if self.definition_version_id.state != "published":
            raise WorkflowConfigurationError(_("Only published workflow definition versions can be started."))

        now = fields.Datetime.now()
        if self.definition_version_id.effective_from_utc and self.definition_version_id.effective_from_utc > now:
            raise WorkflowConfigurationError(_("Workflow definition version is not yet effective."))
        if self.definition_version_id.effective_to_utc and self.definition_version_id.effective_to_utc <= now:
            raise WorkflowConfigurationError(_("Workflow definition version is no longer effective."))

        compiled_artifact = self.definition_version_id.compiled_id
        if not compiled_artifact:
            raise WorkflowConfigurationError(_("Published workflow definition versions require a compiled artifact."))
        if self.definition_version_id.bpmn_hash and compiled_artifact.bpmn_hash != self.definition_version_id.bpmn_hash:
            raise WorkflowConfigurationError(_("Compiled artifact hash does not match the pinned workflow version."))
        self._get_start_node_spec(self._get_compiled_artifact())

    def _acquire_instance_lock(self):
        """Acquire the PostgreSQL advisory transaction lock for this instance."""
        self.ensure_one()
        config = self.env["ir.config_parameter"].sudo()
        timeout_ms = int(config.get_param("daw.lock_timeout_ms", default="10000"))
        retry_count = int(config.get_param("daw.lock_retry_count", default="3"))
        backoff_base_ms = int(config.get_param("daw.lock_backoff_base_ms", default="100"))
        lock_key = self._get_advisory_lock_key()
        deadline = time.monotonic() + (max(timeout_ms, 0) / 1000.0)

        for attempt in range(retry_count + 1):
            # DIRECT_SQL: SDS §6.4 requires PostgreSQL advisory transaction locks for per-instance serialization.
            self.env.cr.execute("SELECT pg_try_advisory_xact_lock(%s)", [lock_key])
            acquired = self.env.cr.fetchone()[0]
            if acquired:
                return True
            if attempt >= retry_count or time.monotonic() >= deadline:
                break

            remaining_seconds = max(deadline - time.monotonic(), 0.0)
            sleep_seconds = min((backoff_base_ms * (attempt + 1)) / 1000.0, remaining_seconds)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        raise WorkflowLockTimeoutError(
            _("Could not acquire workflow runtime lock for instance '%s'.") % (self.display_name or self.id)
        )

    def _get_advisory_lock_key(self):
        """Return a deterministic signed 64-bit advisory lock key."""
        self.ensure_one()
        key_source = ("workflow.instance:%s" % self.id).encode("ascii")
        return int.from_bytes(hashlib.sha256(key_source).digest()[:8], byteorder="big", signed=True)

    def _get_compiled_artifact(self):
        """Load and validate the compiled runtime artifact JSON."""
        self.ensure_one()
        compiled_artifact = self.definition_version_id.compiled_id
        if not compiled_artifact:
            raise WorkflowConfigurationError(_("Workflow instance is missing the compiled runtime artifact."))
        try:
            runtime_artifact = json.loads(compiled_artifact.compiled_data or "{}")
        except JSONDecodeError as err:
            raise WorkflowConfigurationError(_("Compiled workflow artifact must contain valid JSON.")) from err
        if not isinstance(runtime_artifact, dict):
            raise WorkflowConfigurationError(_("Compiled workflow artifact must be a JSON object."))
        return runtime_artifact

    def _get_target_record(self):
        """Return the business record targeted by the workflow instance."""
        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise WorkflowRuntimeError(_("Workflow instance is missing its target record reference."))
        if self.res_model not in self.env:
            raise WorkflowRuntimeError(_("Workflow instance target model '%s' is not installed.") % self.res_model)
        actor_user = self._get_runtime_actor_user()
        target_record = self.env[self.res_model].with_user(actor_user).browse(self.res_id).exists()
        if not target_record:
            raise WorkflowRuntimeError(_("Workflow instance target record no longer exists."))
        return target_record

    def _run_runtime_loop(self, runtime_artifact, target_record, binding_context):
        """Advance active tokens until the runtime reaches a stable state."""
        self.ensure_one()
        for iteration in range(100):
            progress_made = False
            active_tokens = self.env["workflow.token"].search(
                [("instance_id", "=", self.id), ("state", "=", "active")],
                order="id",
            )
            if not active_tokens:
                return

            for token in active_tokens:
                if token.state != "active":
                    continue
                if self._process_active_token(token, runtime_artifact, target_record, binding_context):
                    progress_made = True

            if not progress_made:
                return

        raise WorkflowRuntimeError(_("Runtime tick exceeded the deterministic safety limit."))

    def _process_active_token(self, token, runtime_artifact, target_record, binding_context):
        """Process one active token against the compiled runtime artifact."""
        self.ensure_one()
        if not token.node_runtime_id:
            raise WorkflowRuntimeError(_("Active workflow token is missing its current node runtime."))
        node_runtime = token.node_runtime_id
        if node_runtime.state != "active":
            return False

        node_spec = self._get_node_spec(runtime_artifact, node_runtime.node_id)
        node_type = node_spec["type"]
        if node_type in self._wait_state_by_node_type:
            return self._ensure_wait_artifacts(node_runtime, node_spec)

        if node_type == "end_event":
            self._complete_node_runtime(node_runtime)
            token._consume()
            final_state = self._normalize_final_state(node_spec)
            self._transition_state(final_state)
            self._dispatch_post_commit(
                [
                    {
                        "event_type": "workflow.instance.completed",
                        "instance_id": self.id,
                        "final_state": final_state,
                        "node_id": node_spec["id"],
                    }
                ]
            )
            return True

        if node_type not in {"start_event", "exclusive_gateway", "parallel_gateway"}:
            raise WorkflowConfigurationError(_("Unsupported runtime node type '%s'.") % node_type)
        return bool(token._advance(runtime_artifact, target_record=target_record, binding_context=binding_context))

    def _resolve_outgoing_paths(self, runtime_artifact, node_spec, target_record, binding_context):
        """Resolve the next runtime path or paths for the current node."""
        self.ensure_one()
        outgoing_paths = self._get_outgoing_paths(runtime_artifact, node_spec)
        if node_spec["type"] != "exclusive_gateway":
            return outgoing_paths

        default_path = None
        for path in outgoing_paths:
            if path["is_default"]:
                default_path = path
                continue

            evaluation = self._evaluate_gate_condition(path, target_record, binding_context)
            if evaluation is None:
                return [path]
            if evaluation:
                return [path]

        if default_path:
            return [default_path]
        raise WorkflowRuntimeError(_("Exclusive gateway '%s' has no matching outgoing path.") % node_spec["id"])

    def _get_node_spec(self, runtime_artifact, node_id):
        """Return a normalized node specification from the compiled artifact."""
        self.ensure_one()
        node_index = self._build_node_index(runtime_artifact)
        node_spec = node_index.get(node_id)
        if not node_spec:
            raise WorkflowConfigurationError(_("Compiled workflow artifact is missing node '%s'.") % node_id)
        return node_spec

    def _get_start_node_spec(self, runtime_artifact):
        """Return the normalized start node definition."""
        self.ensure_one()
        node_index = self._build_node_index(runtime_artifact)
        start_node_id = runtime_artifact.get("start_node_id")
        if start_node_id:
            node_spec = node_index.get(start_node_id)
            if not node_spec:
                raise WorkflowConfigurationError(_("Compiled workflow start node '%s' does not exist.") % start_node_id)
            return node_spec

        for node_spec in node_index.values():
            if node_spec["type"] == "start_event":
                return node_spec
        raise WorkflowConfigurationError(_("Compiled workflow artifact must define one start node."))

    def _build_node_index(self, runtime_artifact):
        """Build a normalized node index from the compiled runtime artifact."""
        self.ensure_one()
        raw_nodes = runtime_artifact.get("nodes") or []
        if isinstance(raw_nodes, dict):
            normalized_nodes = []
            for node_id, node_spec in raw_nodes.items():
                current_spec = dict(node_spec or {})
                current_spec.setdefault("id", node_id)
                normalized_nodes.append(current_spec)
            raw_nodes = normalized_nodes
        if not isinstance(raw_nodes, list):
            raise WorkflowConfigurationError(_("Compiled workflow nodes must be a list or object."))

        node_index = {}
        for node_spec in raw_nodes:
            if not isinstance(node_spec, dict):
                raise WorkflowConfigurationError(_("Compiled workflow node definitions must be JSON objects."))
            node_id = node_spec.get("id") or node_spec.get("node_id")
            node_type = node_spec.get("type") or node_spec.get("node_type")
            if not node_id or not node_type:
                raise WorkflowConfigurationError(_("Compiled workflow nodes must include both id and type."))
            normalized_spec = dict(node_spec)
            normalized_spec["id"] = node_id
            normalized_spec["type"] = node_type
            node_index[node_id] = normalized_spec
        return node_index

    def _get_outgoing_paths(self, runtime_artifact, node_spec):
        """Return normalized outgoing path definitions for a node."""
        self.ensure_one()
        raw_paths = node_spec.get("outgoing") or node_spec.get("paths") or []
        if raw_paths:
            return sorted(
                [self._normalize_path_spec(raw_path, position) for position, raw_path in enumerate(raw_paths, start=1)],
                key=lambda path: (path["sequence"], path["target_node_id"]),
            )

        raw_transitions = runtime_artifact.get("transitions") or runtime_artifact.get("edges") or []
        if not isinstance(raw_transitions, list):
            raise WorkflowConfigurationError(_("Compiled workflow transitions must be a list."))

        transitions = []
        for position, transition in enumerate(raw_transitions, start=1):
            if not isinstance(transition, dict):
                raise WorkflowConfigurationError(_("Compiled workflow transitions must be JSON objects."))
            source_node_id = transition.get("source_node_id") or transition.get("source") or transition.get("sourceRef")
            if source_node_id == node_spec["id"]:
                transitions.append(self._normalize_path_spec(transition, position))

        return sorted(transitions, key=lambda path: (path["sequence"], path["target_node_id"]))

    def _normalize_path_spec(self, raw_path, default_sequence):
        """Normalize one compiled path definition into the runtime contract."""
        self.ensure_one()
        if isinstance(raw_path, str):
            return {
                "target_node_id": raw_path,
                "sequence": default_sequence,
                "is_default": False,
                "condition_rule_id": False,
            }
        if not isinstance(raw_path, dict):
            raise WorkflowConfigurationError(_("Compiled workflow paths must be strings or JSON objects."))

        target_node_id = (
            raw_path.get("target_node_id")
            or raw_path.get("target")
            or raw_path.get("targetRef")
            or raw_path.get("node_id")
        )
        if not target_node_id:
            raise WorkflowConfigurationError(_("Compiled workflow path is missing its target node id."))

        return {
            "target_node_id": target_node_id,
            "sequence": raw_path.get("sequence") or default_sequence,
            "is_default": bool(raw_path.get("is_default") or raw_path.get("default")),
            "condition_rule_id": raw_path.get("condition_rule_id"),
            "source_node_id": raw_path.get("source_node_id") or raw_path.get("source") or raw_path.get("sourceRef"),
            "condition_values": raw_path.get("condition")
            or {
                key: raw_path[key]
                for key in ("name", "condition_type", "domain_filter", "python_code", "is_default")
                if key in raw_path
            },
        }

    def _activate_path(self, parent_token, runtime_artifact, path_spec):
        """Activate one downstream node and child token."""
        self.ensure_one()
        target_node_spec = self._get_node_spec(runtime_artifact, path_spec["target_node_id"])
        node_runtime = self._create_node_runtime(target_node_spec)
        self.env["workflow.token"].create(
            {
                "instance_id": self.id,
                "node_runtime_id": node_runtime.id,
                "parent_token_id": parent_token.id,
            }
        )

    def _create_node_runtime(self, node_spec):
        """Create an active node runtime for the supplied node spec."""
        self.ensure_one()
        return self.env["workflow.node.runtime"].create(
            {
                "instance_id": self.id,
                "node_id": node_spec["id"],
                "node_type": node_spec["type"],
                "state": "active",
                "sequence": self._next_node_sequence(),
                "activated_at_utc": fields.Datetime.now(),
            }
        )

    def _next_node_sequence(self):
        """Return the next deterministic sequence value for node runtimes."""
        self.ensure_one()
        latest_runtime = self.env["workflow.node.runtime"].search(
            [("instance_id", "=", self.id)],
            order="sequence desc, id desc",
            limit=1,
        )
        return (latest_runtime.sequence or 0) + 10

    def _ensure_wait_artifacts(self, node_runtime, node_spec):
        """Create task artifacts for wait nodes that need them."""
        self.ensure_one()
        if node_spec["type"] != "user_task":
            return False

        existing_task = self.env["workflow.task"].search(
            [
                ("instance_id", "=", self.id),
                ("node_runtime_id", "=", node_runtime.id),
                ("status", "not in", ("completed", "cancelled")),
            ],
            limit=1,
        )
        if existing_task:
            return False

        self.env["workflow.task"].create(
            {
                "name": node_spec.get("name") or node_spec.get("label") or node_spec["id"],
                "instance_id": self.id,
                "node_runtime_id": node_runtime.id,
            }
        )
        return True

    def _complete_node_runtime(self, node_runtime):
        """Transition an active node runtime to completed."""
        self.ensure_one()
        if node_runtime.state == "completed":
            return
        node_runtime.write(
            {
                "state": "completed",
            }
        )

    def _consume_token(self, token):
        """Mark the active token as consumed."""
        self.ensure_one()
        if token.state != "active":
            return
        token.write(
            {
                "state": "consumed",
                "consumed_at_utc": fields.Datetime.now(),
            }
        )

    def _cancel_active_runtime_records(self):
        """Cancel open tokens, tasks, and node runtimes for the instance."""
        self.ensure_one()
        active_tokens = self.env["workflow.token"].search([("instance_id", "=", self.id), ("state", "=", "active")])
        if active_tokens:
            active_tokens.write(
                {
                    "state": "cancelled",
                    "cancel_reason": "instance_cancelled",
                }
            )

        open_tasks = self.env["workflow.task"].search(
            [
                ("instance_id", "=", self.id),
                ("status", "not in", ("completed", "cancelled")),
            ]
        )
        if open_tasks:
            open_tasks.write({"status": "cancelled"})

        active_runtimes = self.env["workflow.node.runtime"].search(
            [
                ("instance_id", "=", self.id),
                ("state", "in", ("pending", "active")),
            ]
        )
        if active_runtimes:
            active_runtimes.write({"state": "skipped"})

    def _handle_tick_failure(self, err):
        """Persist the incident state after an engine failure."""
        self.ensure_one()
        if isinstance(err, WorkflowConfigurationError):
            reason_code = "runtime_configuration_error"
        elif isinstance(err, WorkflowRuntimeError):
            reason_code = "runtime_tick_failed"
        else:
            reason_code = "runtime_unexpected_error"

        self._record_runtime_incident(reason_code, str(err) or _("Workflow runtime failed."))
        if self.state not in self._terminal_states:
            self._transition_state("error_incident")
        self._dispatch_post_commit(
            [{"event_type": "workflow.instance.incidented", "instance_id": self.id, "reason_code": reason_code}]
        )

    def _record_runtime_incident(self, reason_code, description):
        """Create a runtime incident linked to this workflow instance."""
        self.ensure_one()
        self.env["workflow.incident"].create(
            {
                "instance_id": self.id,
                "category": "integrity_failure",
                "severity": "high",
                "reason_code": reason_code,
                "description": description,
                "correlation_id": self.correlation_id,
                "company_id": self.company_id.id,
            }
        )

    def _transition_state(self, target_state):
        """Apply a validated instance state transition."""
        self.ensure_one()
        if self.state == target_state:
            if target_state in self._terminal_states and not self.ended_at_utc:
                self.write({"ended_at_utc": fields.Datetime.now()})
            return False
        if self.state in self._terminal_states:
            raise WorkflowRuntimeError(_("Workflow instance is already terminal."))
        if target_state not in self._allowed_state_transitions.get(self.state, frozenset()):
            raise WorkflowRuntimeError(
                _("Workflow instance cannot transition from '%(source)s' to '%(target)s'.")
                % {"source": self.state, "target": target_state}
            )

        values = {"state": target_state}
        if target_state in self._terminal_states:
            values["ended_at_utc"] = fields.Datetime.now()
        self.write(values)
        return True

    def _derive_terminal_state(self, runtime_artifact=None):
        """Derive the terminal instance state from completed end nodes."""
        self.ensure_one()
        runtime_artifact = runtime_artifact or self._get_compiled_artifact()
        completed_end_nodes = self.env["workflow.node.runtime"].search(
            [
                ("instance_id", "=", self.id),
                ("node_type", "=", "end_event"),
                ("state", "=", "completed"),
            ]
        )
        if not completed_end_nodes:
            return False

        final_states = {
            self._normalize_final_state(self._get_node_spec(runtime_artifact, node_runtime.node_id))
            for node_runtime in completed_end_nodes
        }
        if "completed_rejected" in final_states:
            return "completed_rejected"
        return "completed_approved"

    def _normalize_final_state(self, node_spec):
        """Map compiled end-node metadata to the instance terminal state."""
        self.ensure_one()
        final_state = node_spec.get("final_state")
        if final_state in self._terminal_states:
            return final_state

        outcome = (node_spec.get("outcome") or node_spec.get("result") or "approve").lower()
        if outcome in {"reject", "rejected", "completed_rejected"}:
            return "completed_rejected"
        return "completed_approved"

    def _has_blocking_incident(self):
        """Return whether the instance still has unresolved blocking incidents."""
        self.ensure_one()
        return bool(
            self.env["workflow.incident"].search_count(
                [
                    ("instance_id", "=", self.id),
                    ("state", "in", ("open", "triaged", "retry_scheduled")),
                ]
            )
        )

    def _has_open_human_task(self):
        """Return whether the instance has any open human task."""
        self.ensure_one()
        return bool(
            self.env["workflow.task"].search_count(
                [
                    ("instance_id", "=", self.id),
                    ("status", "not in", ("completed", "cancelled")),
                ]
            )
        )

    def _has_active_timer_node(self):
        """Return whether the instance is currently waiting on a timer node."""
        self.ensure_one()
        return bool(
            self.env["workflow.node.runtime"].search_count(
                [
                    ("instance_id", "=", self.id),
                    ("node_type", "=", "timer_event"),
                    ("state", "=", "active"),
                ]
            )
        )

    def _has_active_runtime(self):
        """Return whether any token or node runtime is still active."""
        self.ensure_one()
        active_token_count = self.env["workflow.token"].search_count(
            [("instance_id", "=", self.id), ("state", "=", "active")]
        )
        if active_token_count:
            return True
        return bool(
            self.env["workflow.node.runtime"].search_count(
                [
                    ("instance_id", "=", self.id),
                    ("state", "=", "active"),
                ]
            )
        )
