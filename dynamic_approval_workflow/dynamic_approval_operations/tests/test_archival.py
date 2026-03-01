from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestArchival(TransactionCase):
    """Tests for workflow.archive.job.

    Covers: DFR-09-005, SDS §14
    """

    def test_create_archive_job(self):
        """Create an archive job record."""
        job = self.env["workflow.archive.job"].create(
            {
                "job_type": "archive",
            }
        )
        self.assertTrue(job.id)
        self.assertEqual(job.state, "pending")
