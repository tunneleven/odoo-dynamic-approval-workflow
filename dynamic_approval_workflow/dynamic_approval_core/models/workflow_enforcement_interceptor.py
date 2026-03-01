from odoo import models


class WorkflowEnforcementInterceptor(models.AbstractModel):
    """ORM enforcement interceptor — ``_patch_method`` wrapper logic.

    Wraps bound model methods at registry load time to enforce
    workflow gates across all channels (UI, RPC, import, cron, sudo).

    This is an abstract model; it does not create a database table.

    SDS: §7 ORM Interceptor Design
    SRS: FR-008, FR-090..FR-092  |  DFR: DFR-02-002..DFR-02-011
    ADR: ADR-002
    """

    _name = "workflow.enforcement.interceptor"
    _description = "Workflow Enforcement Interceptor"
