{
    "name": "Dynamic Approval Workflow — Operations",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Monitoring, retention, and archival for Dynamic Approval Workflow",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dynamic-approval-workflow",
    "license": "AGPL-3",
    "depends": [
        "dynamic_approval_core",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/workflow_operations_dashboard.xml",
        "views/workflow_retention_views.xml",
        "views/menu_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "development_status": "Alpha",
    "maintainers": [],
}
