from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WorkflowFollowerRule(models.Model):
    """Auto-follower management rules for workflow-bound records.

    SRS: FR-027  |  SDS: §3.4
    """

    _name = "workflow.follower.rule"
    _description = "Workflow Follower Rule"
    _order = "sequence"

    name = fields.Char(size=128, required=True)
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    follower_type = fields.Selection(
        [
            ("requester", "Requester"),
            ("approver", "Current Approvers"),
            ("group", "Security Group"),
            ("field", "Record Field"),
        ],
        required=True,
    )
    group_id = fields.Many2one(
        "res.groups",
        ondelete="restrict",
    )
    field_path = fields.Char(size=255)
    completion_policy = fields.Selection(
        [
            ("retained", "Retained"),
            ("downgraded", "Downgraded"),
            ("removed", "Removed"),
        ],
        default="retained",
    )
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    @api.constrains("follower_type", "group_id", "field_path")
    def _check_follower_type_values(self):
        """Validate required field based on follower_type."""
        for record in self:
            if record.follower_type == "group" and not record.group_id:
                raise ValidationError(_("Group is required when follower type is 'group'."))
            if record.follower_type == "field" and not record.field_path:
                raise ValidationError(_("Field path is required when follower type is 'field'."))

    def _resolve_followers(self, requester=None, approvers=None, record=None):
        """Resolve followers for this rule as a res.users recordset."""
        self.ensure_one()
        empty_users = self.env["res.users"]
        if self.follower_type == "requester":
            return requester if requester else empty_users
        if self.follower_type == "approver":
            return approvers if approvers else empty_users
        if self.follower_type == "group":
            return self.group_id.user_ids | self.group_id.all_user_ids
        if self.follower_type == "field":
            if not record:
                return empty_users
            return self._resolve_users_from_field_path(record)
        return empty_users

    def _resolve_users_from_field_path(self, record):
        """Resolve res.users from a dot-separated field path on the target record."""
        self.ensure_one()
        current = record
        for field_name in (self.field_path or "").split("."):
            if not field_name:
                continue
            if field_name not in current._fields:
                raise ValidationError(_("Invalid field path segment '%s'.") % field_name)
            current = current.mapped(field_name)
            if not current:
                return self.env["res.users"]

        if current._name == "res.users":
            return current
        return self.env["res.users"]
