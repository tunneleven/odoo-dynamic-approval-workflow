{
    "name": "Dynamic Approval Workflow — BPMN Designer",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "BPMN diagram modeler and viewer for Dynamic Approval Workflow",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dynamic-approval-workflow",
    "license": "AGPL-3",
    "depends": [
        "dynamic_approval_core",
        "web",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/workflow_bpmn_security.xml",
        "views/workflow_diagram_views.xml",
        "views/menu_views.xml",
    ],
    "assets": {
        "dynamic_approval_bpmn.bpmn_assets": [
            "dynamic_approval_bpmn/static/lib/bpmn-js/**/*",
        ],
        "web.assets_backend": [
            "dynamic_approval_bpmn/static/src/**/*",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "development_status": "Alpha",
    "maintainers": [],
}
