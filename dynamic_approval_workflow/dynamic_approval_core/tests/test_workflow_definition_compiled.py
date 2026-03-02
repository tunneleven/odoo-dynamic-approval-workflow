from odoo.addons.dynamic_approval_core.exceptions import WorkflowError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowDefinitionCompiled(TransactionCase):
    """Tests for workflow.definition.compiled immutability enforcement.

    Validates FR-015  |  DFR: DFR-01-005, DFR-03-003
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.compiled = cls.env["workflow.definition.compiled"].create(
            {
                "bpmn_hash": "a" * 64,
                "compiled_data": '{"nodes": []}',
                "node_count": 1,
                "gateway_count": 0,
            }
        )

    def test_create_succeeds(self):
        """Validates FR-015: create() is permitted; immutability does not block initial creation."""
        record = self.env["workflow.definition.compiled"].create(
            {
                "bpmn_hash": "b" * 64,
                "compiled_data": '{"nodes": []}',
            }
        )
        self.assertTrue(record.id, "create() should succeed for a new compiled artifact")

    def test_write_raises_workflow_error(self):
        """Validates FR-015: write() is blocked — compiled artifacts are immutable after creation."""
        with self.assertRaises(WorkflowError, msg="write() must raise WorkflowError on compiled artifact"):
            self.compiled.write({"node_count": 99})

    def test_unlink_raises_workflow_error(self):
        """Validates FR-015: unlink() is blocked — compiled artifacts are immutable after creation."""
        record = self.env["workflow.definition.compiled"].create(
            {
                "bpmn_hash": "c" * 64,
                "compiled_data": '{"nodes": []}',
            }
        )
        with self.assertRaises(WorkflowError, msg="unlink() must raise WorkflowError on compiled artifact"):
            record.unlink()
