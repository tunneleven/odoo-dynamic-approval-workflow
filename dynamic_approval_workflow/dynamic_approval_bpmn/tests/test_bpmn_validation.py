from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBpmnValidation(TransactionCase):
    """Tests for BPMN diagram validation.

    Covers: DFR-03-005, FR-018
    """

    def test_validation_result_creation(self):
        """Validation result records can be created."""
        definition = self.env["workflow.definition"].create(
            {
                "name": "BPMN Test WF",
                "definition_key": "bpmn_test_wf",
            }
        )
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
            }
        )
        result = self.env["workflow.diagram.validation.result"].create(
            {
                "definition_version_id": version.id,
                "element_id": "StartEvent_1",
                "error_category": "structural",
                "error_code": "MISSING_OUTGOING",
                "message": "Start event has no outgoing sequence flow.",
            }
        )
        self.assertTrue(result.id)
        self.assertEqual(result.severity, "error")
