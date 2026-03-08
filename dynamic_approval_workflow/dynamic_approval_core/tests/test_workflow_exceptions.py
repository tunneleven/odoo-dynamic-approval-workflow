from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..exceptions import (
    WorkflowCallbackError,
    WorkflowConfigurationError,
    WorkflowError,
    WorkflowGateBlockedError,
    WorkflowIdempotencyConflictError,
    WorkflowIntegrityError,
    WorkflowLockTimeoutError,
    WorkflowRuntimeError,
    WorkflowSecurityPolicyError,
)


@tagged("post_install", "-at_install")
class TestWorkflowExceptions(TransactionCase):
    """Tests for the workflow exception hierarchy contract."""

    def test_exception_hierarchy_matches_sds_contract(self):
        """Validate the typed workflow exception inheritance tree."""
        hierarchy = (
            (WorkflowError, UserError),
            (WorkflowGateBlockedError, WorkflowError),
            (WorkflowConfigurationError, WorkflowError),
            (WorkflowRuntimeError, WorkflowError),
            (WorkflowLockTimeoutError, WorkflowRuntimeError),
            (WorkflowCallbackError, WorkflowError),
            (WorkflowIdempotencyConflictError, WorkflowError),
            (WorkflowIntegrityError, WorkflowError),
            (WorkflowSecurityPolicyError, WorkflowError),
        )

        for exception_class, parent_class in hierarchy:
            self.assertTrue(
                issubclass(exception_class, parent_class),
                "%s must inherit from %s."
                % (exception_class.__name__, parent_class.__name__),
            )

    def test_exception_message_passthrough(self):
        """Validate workflow exceptions preserve the supplied user-facing message."""
        message = "Action is blocked by workflow policy."

        error = WorkflowGateBlockedError(message)

        self.assertEqual(
            str(error),
            message,
            "Workflow exceptions should preserve the original error message.",
        )
