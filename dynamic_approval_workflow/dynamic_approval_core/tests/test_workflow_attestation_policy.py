from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowAttestationPolicy(TransactionCase):
    """Tests for workflow.attestation.policy model contract."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Attestation Workflow",
                "definition_key": "attestation_wf",
            }
        )
        cls.definition_version = cls.env["workflow.definition.version"].create(
            {
                "definition_id": cls.definition.id,
                "bpmn_xml": "<xml/>",
            }
        )

    def test_field_contract_matches_task(self):
        fields_map = self.env["workflow.attestation.policy"]._fields
        expected_fields = {
            "name",
            "definition_version_id",
            "node_id",
            "signature_required",
            "attestation_type",
            "legal_human_signature_required",
            "allow_system_attestation_on_timeout",
            "required_evidence_types",
            "capture_methods",
            "company_id",
        }
        self.assertTrue(
            expected_fields.issubset(fields_map),
            "workflow.attestation.policy is missing one or more required fields for TASK-P1-006",
        )

    def test_create_policy_with_comma_separated_fields(self):
        policy = self.env["workflow.attestation.policy"].create(
            {
                "name": "Invoice Legal Signature",
                "definition_version_id": self.definition_version.id,
                "node_id": "UserTask_LegalSign",
                "attestation_type": "human_signature",
                "required_evidence_types": "signature,image,audit_log",
                "capture_methods": "ui_upload,pad,external_provider",
            }
        )
        self.assertEqual(policy.required_evidence_types, "signature,image,audit_log")
        self.assertEqual(policy.capture_methods, "ui_upload,pad,external_provider")
        self.assertFalse(policy.signature_required)
        self.assertFalse(policy.legal_human_signature_required)
        self.assertFalse(policy.allow_system_attestation_on_timeout)

    def test_legal_signature_blocks_system_timeout_attestation(self):
        with self.assertRaises(ValidationError):
            self.env["workflow.attestation.policy"].create(
                {
                    "name": "Legal Step",
                    "definition_version_id": self.definition_version.id,
                    "node_id": "UserTask_Legal",
                    "legal_human_signature_required": True,
                    "allow_system_attestation_on_timeout": True,
                }
            )

    def test_definition_version_delete_cascades_policy(self):
        definition = self.env["workflow.definition"].create(
            {
                "name": "Cascade Workflow",
                "definition_key": "cascade_wf",
            }
        )
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
                "bpmn_xml": "<xml/>",
            }
        )
        policy = self.env["workflow.attestation.policy"].create(
            {
                "name": "Cascade Policy",
                "definition_version_id": version.id,
                "node_id": "UserTask_Cascade",
            }
        )

        version.unlink()

        remaining = self.env["workflow.attestation.policy"].search_count([("id", "=", policy.id)])
        self.assertEqual(remaining, 0, "Deleting definition version must cascade-delete attestation policies")
