import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..exceptions import WorkflowRuntimeError


class WorkflowToken(models.Model):
    """Branch progress marker through sequence flows.

    Tokens are **never deleted** — state transitions only
    (``active`` → ``consumed`` / ``cancelled``).

    SDS: §6.6 Token Management
    SRS: FR-021, FR-022, FR-025  |  DFR: DFR-04-013
    """

    _name = "workflow.token"
    _description = "Workflow Token"
    _order = "instance_id, create_date"

    _allowed_state_transitions = {
        "active": {"consumed", "cancelled"},
        "consumed": set(),
        "cancelled": set(),
    }
    _managed_timestamp_fields = {"consumed_at_utc"}
    _immutable_identity_fields = {"instance_id", "parent_token_id", "branch_id"}

    instance_id = fields.Many2one(
        "workflow.instance",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
    )
    node_runtime_id = fields.Many2one(
        "workflow.node.runtime",
        string="Current Node",
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
        string="Branch ID",
        index=True,
        readonly=True,
        help="Parallel branch label assigned by _fork; siblings share a common prefix.",
    )
    state = fields.Selection(
        [
            ("active", "Active"),
            ("consumed", "Consumed"),
            ("cancelled", "Cancelled"),
        ],
        default="active",
        required=True,
        index=True,
    )
    cancel_reason = fields.Selection(
        [
            ("branch_superseded", "Branch Superseded"),
            ("instance_cancelled", "Instance Cancelled"),
            ("rework", "Rework Loop"),
        ],
    )
    created_at_utc = fields.Datetime(
        string="Created At",
        default=fields.Datetime.now,
        readonly=True,
    )
    consumed_at_utc = fields.Datetime(
        string="Consumed At",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="instance_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    # SECURITY: workflow.token records are immutable audit artifacts.
    # Deletion would corrupt the runtime execution history and break
    # parallel branch tracking (parent/child lineage for fork/join).
    # This override provides a fail-closed in-process guard.
    # ACL enforcement: ir.model.access.csv grants perm_unlink=0 for all
    # roles (token.admin row col 7 = 0; no unlink ACL for auditor).
    # Both layers are required: ACL prevents direct ORM calls from UI/API;
    # this override prevents bypasses from internal sudo() call sites.
    def unlink(self):
        raise UserError(
            _("Workflow tokens cannot be deleted. Use state transitions instead.")
        )

    def write(self, vals):
        """Enforce the token state machine, identity immutability, and managed timestamps."""
        vals = dict(vals)

        attempted_identity_updates = self._immutable_identity_fields.intersection(vals)
        if attempted_identity_updates:
            raise ValidationError(
                _("Workflow token identity fields are immutable after creation.")
            )

        provided_timestamps = self._managed_timestamp_fields.intersection(vals)
        if provided_timestamps:
            raise ValidationError(
                _("Token consumption timestamps are managed by state transitions.")
            )

        state = vals.get("state")
        if state is None:
            return super().write(vals)

        same_state_records = self.filtered(lambda r: r.state == state)
        transition_records = self - same_state_records
        result = True

        if same_state_records:
            non_state_vals = {k: v for k, v in vals.items() if k != "state"}
            if non_state_vals:
                result = super(WorkflowToken, same_state_records).write(non_state_vals) and result

        if transition_records:
            transition_records._validate_state_transition(state)
            transition_vals = dict(vals)
            if state == "consumed":
                transition_vals["consumed_at_utc"] = fields.Datetime.now()
            result = super(WorkflowToken, transition_records).write(transition_vals) and result

        return result

    def _validate_state_transition(self, next_state):
        """Validate a requested state change against the token state machine."""
        for record in self:
            current_state = record.state
            if current_state == next_state:
                continue
            allowed = self._allowed_state_transitions.get(current_state, set())
            if next_state not in allowed:
                raise ValidationError(
                    _("Invalid token transition from '%(source)s' to '%(target)s'.")
                    % {"source": current_state, "target": next_state}
                )

    @api.constrains("state", "consumed_at_utc")
    def _check_state_timestamps(self):
        """Keep timestamp invariants aligned with the token state machine."""
        for record in self:
            if record.state == "consumed" and not record.consumed_at_utc:
                raise ValidationError(
                    _("Consumed tokens must have a consumption timestamp.")
                )
            if record.state == "active" and record.consumed_at_utc:
                raise ValidationError(
                    _("Active tokens cannot have a consumption timestamp.")
                )
            if record.state == "cancelled" and record.consumed_at_utc:
                raise ValidationError(
                    _("Cancelled tokens cannot have a consumption timestamp.")
                )

    @api.constrains("state", "cancel_reason")
    def _check_cancel_reason(self):
        """Ensure cancelled tokens have a reason and active/consumed do not."""
        for record in self:
            if record.state == "cancelled" and not record.cancel_reason:
                raise ValidationError(
                    _("Cancelled tokens must have a cancel reason.")
                )
            if record.state != "cancelled" and record.cancel_reason:
                raise ValidationError(
                    _("Only cancelled tokens can have a cancel reason.")
                )

    # ------------------------------------------------------------------
    # Token operations — SDS §6.6
    # ------------------------------------------------------------------

    def _consume(self):
        """Mark active tokens as consumed.

        Sets state to ``consumed`` and records the consumption timestamp
        (auto-managed by ``write()``). Operates on the full recordset.
        """
        non_active = self.filtered(lambda t: t.state != "active")
        if non_active:
            raise WorkflowRuntimeError(
                _("Only active tokens can be consumed.")
            )
        self.write({"state": "consumed"})

    def _advance(self, target_node_runtime):
        """Consume this token and create one downstream child token.

        Used for sequential flow: consume current → create one downstream.

        :param target_node_runtime: ``workflow.node.runtime`` record for
            the next node in the sequence.
        :returns: newly created child token at the target node.
        """
        self.ensure_one()
        if target_node_runtime.instance_id != self.instance_id:
            raise WorkflowRuntimeError(
                _("Target node runtime belongs to a different workflow instance.")
            )
        self._consume()
        return self.create({
            "instance_id": self.instance_id.id,
            "node_runtime_id": target_node_runtime.id,
            "parent_token_id": self.id,
        })

    def _fork(self, target_node_runtimes):
        """Consume this token and create N child tokens for parallel split.

        Each child receives a unique ``branch_id`` derived from a shared
        prefix so that sibling tokens can be identified via
        ``parent_token_id`` for join resolution.

        :param target_node_runtimes: recordset of ``workflow.node.runtime``
            records — one child token is created per record.
        :returns: recordset of newly created child tokens.
        """
        self.ensure_one()
        if not target_node_runtimes:
            raise WorkflowRuntimeError(
                _("Parallel fork requires at least one target node runtime.")
            )
        mismatched = target_node_runtimes.filtered(
            lambda nr: nr.instance_id != self.instance_id
        )
        if mismatched:
            raise WorkflowRuntimeError(
                _("Target node runtime belongs to a different workflow instance.")
            )
        self._consume()
        branch_prefix = uuid.uuid4().hex[:16]
        create_vals = [
            {
                "instance_id": self.instance_id.id,
                "node_runtime_id": nr.id,
                "parent_token_id": self.id,
                "branch_id": "%s-%d" % (branch_prefix, idx),
            }
            for idx, nr in enumerate(target_node_runtimes)
        ]
        return self.create(create_vals)

    def _join(self, join_type="all", quorum_threshold=None):
        """Evaluate the join condition for a converging parallel gateway.

        Checks whether sibling tokens (same ``parent_token_id``) satisfy
        the join merge condition. This token must be active and is treated
        as the arriving token (not yet consumed).

        :param join_type: ``'all'`` (default), ``'any'``, or ``'quorum'``.
        :param quorum_threshold: integer count required for ``'quorum'``
            join type. Ignored for ``'all'`` and ``'any'``.
        :returns: ``True`` if the join condition is satisfied and the
            caller should proceed with downstream activation.
            ``False`` if the token must wait for more siblings.

        .. warning::
            Callers must hold the per-instance ``pg_advisory_xact_lock``
            (SDS §6.4) before invoking this method to prevent concurrent
            double-trigger in multi-worker deployments.
        """
        self.ensure_one()
        if self.state != "active":
            return False
        if not self.parent_token_id:
            return True

        siblings = self.search([
            ("parent_token_id", "=", self.parent_token_id.id),
            ("id", "!=", self.id),
        ])

        if join_type == "any":
            self._cancel_remaining_siblings(siblings)
            return True

        if join_type == "quorum":
            # Exclude already-cancelled siblings from denominator to avoid
            # livelock when branches were cancelled upstream.
            live_siblings = siblings.filtered(lambda t: t.state != "cancelled")
            live_branch_count = len(live_siblings) + 1  # +1 for self (arriving)
            effective_threshold = (
                quorum_threshold if quorum_threshold is not None else live_branch_count
            )
            arrived_count = len(
                siblings.filtered(lambda t: t.state == "consumed")
            ) + 1  # +1 for self (arriving, still active)
            if arrived_count >= effective_threshold:
                self._cancel_remaining_siblings(siblings)
                return True
            return False

        # Default: "all" — every live sibling must be consumed.
        # Cancelled siblings are treated as "done" to prevent livelock
        # when branches were cancelled upstream or by a prior join.
        pending_siblings = siblings.filtered(
            lambda t: t.state not in ("consumed", "cancelled")
        )
        return not pending_siblings

    def _cancel_remaining_siblings(self, siblings):
        """Cancel active sibling tokens that are superseded by the join."""
        active_siblings = siblings.filtered(lambda t: t.state == "active")
        if active_siblings:
            active_siblings.write({
                "state": "cancelled",
                "cancel_reason": "branch_superseded",
            })
