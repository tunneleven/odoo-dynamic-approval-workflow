from odoo import api, models


class WorkflowBindingInterceptor(models.Model):
    """Refresh ORM interceptor patches when bindings change."""

    _inherit = "workflow.binding"

    def _refresh_interceptor_patches(self):
        from .workflow_enforcement_interceptor import WorkflowEnforcementInterceptor

        WorkflowEnforcementInterceptor._apply_patches(self.env)

    def _register_hook(self):
        result = super()._register_hook()
        self._refresh_interceptor_patches()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._refresh_interceptor_patches()
        return records

    def write(self, vals):
        result = super().write(vals)
        if self._config_revision_fields.intersection(vals):
            self._refresh_interceptor_patches()
        return result

    def unlink(self):
        result = super().unlink()
        self._refresh_interceptor_patches()
        return result
