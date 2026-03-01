from odoo.exceptions import UserError


class WorkflowError(UserError):
    """Base exception for all workflow errors."""


class WorkflowGateBlockedError(WorkflowError):
    """Action blocked by workflow gate."""


class WorkflowConfigurationError(WorkflowError):
    """Invalid workflow configuration."""


class WorkflowRuntimeError(WorkflowError):
    """Runtime engine failure."""


class WorkflowLockTimeoutError(WorkflowRuntimeError):
    """Per-instance lock acquisition timeout."""


class WorkflowCallbackError(WorkflowError):
    """Callback execution failure."""


class WorkflowIdempotencyConflictError(WorkflowError):
    """Same idempotency key with different payload."""


class WorkflowIntegrityError(WorkflowError):
    """Evidence hash mismatch or data integrity failure."""


class WorkflowSecurityPolicyError(WorkflowError):
    """Security policy violation."""
