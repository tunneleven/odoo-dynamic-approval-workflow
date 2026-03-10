import math
import uuid

from odoo import _, fields, models

from ..exceptions import WorkflowConfigurationError, WorkflowError, WorkflowRuntimeError


class WorkflowToken(models.Model):
    """Branch progress marker through sequence flows.

    Tokens are **never deleted** — state transitions only
    (``active`` → ``consumed`` / ``cancelled``).

    SDS: §6.6 Token Management
    SRS: FR-022, FR-024  |  DFR: DFR-04-013
    """

    _name = "workflow.token"
    _description = "Workflow Token"
    _order = "instance_id, create_date"
    _state_selection = [
        ("active", "Active"),
        ("consumed", "Consumed"),
        ("cancelled", "Cancelled"),
    ]
    _cancel_reason_selection = [
        ("branch_superseded", "Branch Superseded"),
        ("instance_cancelled", "Instance Cancelled"),
        ("rework", "Rework Loop"),
    ]

    instance_id = fields.Many2one(
        "workflow.instance",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
    )
    node_runtime_id = fields.Many2one(
        "workflow.node.runtime",
        ondelete="set null",
        index=True,
    )
    parent_token_id = fields.Many2one(
        "workflow.token",
        string="Parent Token",
        ondelete="set null",
        index=True,
        readonly=True,
    )
    branch_id = fields.Char(
        size=64,
        index=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=_state_selection,
        default="active",
        required=True,
        index=True,
    )
    cancel_reason = fields.Selection(
        selection=_cancel_reason_selection,
    )
    created_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    consumed_at_utc = fields.Datetime(readonly=True)
    company_id = fields.Many2one(
        related="instance_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    # SECURITY: Tokens are immutable audit artifacts for runtime lineage.
    # Hard deletion is blocked at the model layer even if ACLs were ever to
    # allow unlink, so token history remains append-only and traceable.
    def unlink(self):
        """Blocked - tokens are never deleted."""
        raise WorkflowError(_("Workflow tokens are immutable and cannot be deleted."))

    def _advance(self, runtime_artifact, target_record=None, binding_context=None):
        """Advance this token to its next runtime node or join outcome."""
        self.ensure_one()
        if self.state != "active":
            return False
        if not self.node_runtime_id:
            raise WorkflowRuntimeError(_("Active workflow token is missing its current node runtime."))

        instance = self.instance_id
        node_spec = instance._get_node_spec(runtime_artifact, self.node_runtime_id.node_id)
        if node_spec["type"] == "parallel_gateway":
            outgoing_paths = instance._get_outgoing_paths(runtime_artifact, node_spec)
            if self._is_join_gateway(node_spec, outgoing_paths):
                return self._join(runtime_artifact, node_spec=node_spec, outgoing_paths=outgoing_paths)
            if not outgoing_paths:
                raise WorkflowRuntimeError(_("Runtime node '%s' has no reachable outgoing path.") % node_spec["id"])
            instance._complete_node_runtime(self.node_runtime_id)
            self._consume(runtime_artifact=runtime_artifact, outgoing_paths=outgoing_paths)
            return True

        instance._complete_node_runtime(self.node_runtime_id)
        outgoing_paths = instance._resolve_outgoing_paths(
            runtime_artifact,
            node_spec,
            target_record,
            binding_context or {},
        )
        if not outgoing_paths:
            raise WorkflowRuntimeError(_("Runtime node '%s' has no reachable outgoing path.") % node_spec["id"])
        self._consume(runtime_artifact=runtime_artifact, outgoing_paths=outgoing_paths)
        return True

    def _consume(self, runtime_artifact=None, outgoing_paths=None, parent_token=None, branch_id=None):
        """Mark the token consumed and optionally create downstream tokens."""
        self.ensure_one()
        if self.state != "active":
            return self.env["workflow.token"]

        self.write(
            {
                "state": "consumed",
                "consumed_at_utc": fields.Datetime.now(),
            }
        )
        outgoing_paths = list(outgoing_paths or [])
        if not outgoing_paths:
            return self.env["workflow.token"]
        if len(outgoing_paths) > 1:
            return self._fork(runtime_artifact, outgoing_paths)
        return self._spawn_child_token(
            runtime_artifact,
            outgoing_paths[0],
            parent_token=parent_token if parent_token is not None else self,
            branch_id=self.branch_id if branch_id is None else branch_id,
        )

    def _fork(self, runtime_artifact, outgoing_paths):
        """Create one child token per outgoing parallel branch."""
        self.ensure_one()
        child_tokens = self.env["workflow.token"]
        branch_group_id = uuid.uuid4().hex
        for path_spec in outgoing_paths:
            child_tokens |= self._spawn_child_token(
                runtime_artifact,
                path_spec,
                parent_token=self,
                branch_id=branch_group_id,
            )
        return child_tokens

    def _join(self, runtime_artifact, node_spec=None, outgoing_paths=None):
        """Resolve a parallel join when its completion rule is satisfied."""
        self.ensure_one()
        if not self.branch_id:
            raise WorkflowConfigurationError(_("Parallel join token is missing its branch group identifier."))

        split_parent = self._get_split_parent_token()
        if not split_parent:
            raise WorkflowConfigurationError(_("Parallel join token is missing its split-parent lineage."))

        node_spec = node_spec or self.instance_id._get_node_spec(runtime_artifact, self.node_runtime_id.node_id)
        waiting_tokens = self._get_join_waiting_tokens()
        expected_branch_count = self.env["workflow.token"].search_count(
            [
                ("parent_token_id", "=", split_parent.id),
                ("branch_id", "=", self.branch_id),
            ]
        )
        if expected_branch_count <= 0:
            raise WorkflowConfigurationError(_("Parallel join '%s' has no expected branch roots.") % node_spec["id"])

        join_mode = self._get_join_mode(node_spec)
        required_count = self._get_required_join_count(node_spec, expected_branch_count, join_mode)
        if len(waiting_tokens) < required_count:
            return False

        waiting_runtimes = waiting_tokens.mapped("node_runtime_id").filtered(lambda runtime: runtime.state == "active")
        if waiting_runtimes:
            waiting_runtimes.write({"state": "completed"})

        waiting_tokens.write(
            {
                "state": "consumed",
                "consumed_at_utc": fields.Datetime.now(),
            }
        )

        remaining_tokens = self.env["workflow.token"].search(
            [
                ("instance_id", "=", self.instance_id.id),
                ("branch_id", "=", self.branch_id),
                ("state", "=", "active"),
                ("id", "not in", waiting_tokens.ids),
            ]
        )
        self._cancel_branch_tokens(remaining_tokens)

        outgoing_paths = list(outgoing_paths or self.instance_id._get_outgoing_paths(runtime_artifact, node_spec))
        if not outgoing_paths:
            return True
        if len(outgoing_paths) != 1:
            raise WorkflowConfigurationError(
                _("Parallel join '%s' must resolve to exactly one outgoing path.") % node_spec["id"]
            )

        self._spawn_child_token(
            runtime_artifact,
            outgoing_paths[0],
            parent_token=split_parent,
            branch_id=split_parent.branch_id,
        )
        return True

    def _spawn_child_token(self, runtime_artifact, path_spec, parent_token=None, branch_id=None):
        """Create one downstream token and node runtime for a resolved path."""
        self.ensure_one()
        parent_token = parent_token.exists() if parent_token else self.env["workflow.token"]
        target_node_spec = self.instance_id._get_node_spec(runtime_artifact, path_spec["target_node_id"])
        node_runtime = self.instance_id._create_node_runtime(target_node_spec)
        return self.env["workflow.token"].create(
            {
                "instance_id": self.instance_id.id,
                "node_runtime_id": node_runtime.id,
                "parent_token_id": parent_token.id or False,
                "branch_id": branch_id,
            }
        )

    def _is_join_gateway(self, node_spec, outgoing_paths):
        """Return whether the current parallel gateway behaves as a join."""
        self.ensure_one()
        incoming = node_spec.get("incoming") or node_spec.get("incoming_paths") or node_spec.get("incoming_branches")
        incoming_count = self._get_incoming_count(node_spec, incoming)

        gateway_direction = str(node_spec.get("gateway_direction") or node_spec.get("direction") or "").lower()
        if node_spec.get("join_mode") or node_spec.get("quorum_mode"):
            return True
        if gateway_direction in {"converging", "mixed"}:
            return True
        if incoming_count > 1:
            return True
        return bool(self.branch_id and len(outgoing_paths) <= 1 and self._get_split_parent_token())

    def _get_incoming_count(self, node_spec, incoming=None):
        """Return a safe incoming-branch count for join heuristics."""
        self.ensure_one()
        if isinstance(incoming, list):
            return len(incoming)
        if isinstance(incoming, int):
            return max(incoming, 0)
        if isinstance(incoming, str):
            return 1 if incoming else 0

        raw_count = node_spec.get("incoming_count") or 0
        try:
            return max(int(raw_count), 0)
        except (TypeError, ValueError):
            return 0

    def _get_split_parent_token(self):
        """Return the token that existed before the current branch group split."""
        self.ensure_one()
        if not self.branch_id:
            return self.env["workflow.token"]

        token = self
        while token.parent_token_id and token.parent_token_id.branch_id == self.branch_id:
            token = token.parent_token_id
        return token.parent_token_id

    def _get_join_waiting_tokens(self):
        """Return active tokens from the same branch group waiting at this join node."""
        self.ensure_one()
        if not self.node_runtime_id:
            return self.env["workflow.token"]
        return self.env["workflow.token"].search(
            [
                ("instance_id", "=", self.instance_id.id),
                ("branch_id", "=", self.branch_id),
                ("state", "=", "active"),
                ("node_runtime_id.node_id", "=", self.node_runtime_id.node_id),
            ],
            order="id",
        )

    def _get_join_mode(self, node_spec):
        """Return the normalized join mode for a parallel gateway."""
        self.ensure_one()
        join_mode = node_spec.get("join_mode") or node_spec.get("quorum_mode") or "all"
        if join_mode not in {"all", "any", "quorum"}:
            raise WorkflowConfigurationError(
                _("Parallel join '%s' has unsupported mode '%s'.") % (node_spec["id"], join_mode)
            )
        return join_mode

    def _get_required_join_count(self, node_spec, expected_branch_count, join_mode):
        """Return the number of arrived branches required to close the join."""
        self.ensure_one()
        if join_mode == "all":
            return expected_branch_count
        if join_mode == "any":
            return 1

        required_count = int(node_spec.get("quorum_count") or 0)
        quorum_percentage = node_spec.get("quorum_percentage")
        if quorum_percentage not in (None, False, ""):
            required_count = max(required_count, math.ceil(expected_branch_count * float(quorum_percentage) / 100.0))
        if required_count <= 0:
            raise WorkflowConfigurationError(
                _("Parallel quorum join '%s' requires quorum_count or quorum_percentage.") % node_spec["id"]
            )
        if required_count > expected_branch_count:
            raise WorkflowConfigurationError(
                _("Parallel quorum join '%s' requires more branches than exist.") % node_spec["id"]
            )
        return required_count

    def _cancel_branch_tokens(self, tokens):
        """Cancel superseded branch tokens and their open runtime artifacts."""
        if not tokens:
            return

        subtree_tokens = self._collect_descendant_tokens(tokens)
        active_subtree_tokens = subtree_tokens.filtered(lambda token: token.state == "active")
        if not active_subtree_tokens:
            return

        runtime_ids = active_subtree_tokens.mapped("node_runtime_id").ids
        active_subtree_tokens.write(
            {
                "state": "cancelled",
                "cancel_reason": "branch_superseded",
            }
        )

        node_runtimes = active_subtree_tokens.mapped("node_runtime_id").filtered(
            lambda runtime: runtime.state in {"pending", "active"}
        )
        if node_runtimes:
            node_runtimes.write({"state": "skipped"})

        if runtime_ids:
            open_tasks = self.env["workflow.task"].search(
                [
                    ("instance_id", "=", self.instance_id.id),
                    ("node_runtime_id", "in", runtime_ids),
                    ("status", "not in", ("completed", "cancelled")),
                ]
            )
            if open_tasks:
                open_tasks.write({"status": "cancelled"})

    def _collect_descendant_tokens(self, tokens):
        """Return the supplied tokens plus every descendant in their lineage."""
        descendant_tokens = tokens
        frontier = tokens
        while frontier:
            frontier = self.env["workflow.token"].search([("parent_token_id", "in", frontier.ids)])
            descendant_tokens |= frontier
        return descendant_tokens
