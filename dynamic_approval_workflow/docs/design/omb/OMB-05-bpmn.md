# OMB-05 — `dynamic_approval_bpmn` Module Specification

Parent: `OMB-00-index.md`
Module: `dynamic_approval_bpmn`
SDS Reference: `SDS §5`, `ADR-003`
DFR: `DFR-03-001` through `DFR-03-009`

---

## 1. `__manifest__.py`

```python
{
    'name': 'Dynamic Approval BPMN',
    'version': '19.0.1.0.0',
    'category': 'Workflow',
    'summary': 'BPMN modeler and viewer for Dynamic Approval Workflow',
    'description': 'Visual BPMN 2.0 diagram editor and runtime viewer.',
    'author': 'Your Company',
    'website': 'https://github.com/your-org/dynamic-approval-workflow',
    'license': 'LGPL-3',
    'depends': ['dynamic_approval_core', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/workflow_diagram_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dynamic_approval_bpmn/static/lib/bpmn-js/bpmn-modeler.production.min.js',
            'dynamic_approval_bpmn/static/src/components/**/*',
            'dynamic_approval_bpmn/static/src/fields/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
```

> **Third-party dependency (`bpmn.js`):**
> - **Version**: `bpmn.js >= 17.0.0` (target `17.11.x`)
> - **License**: Apache-2.0 (compatible with LGPL-3)
> - **Loading**: Bundled as static asset via `web.assets_backend` key (file: `static/lib/bpmn-js/bpmn-modeler.production.min.js`)
> - **Verification**: Run `npm info bpmn-js version` or check `package.json` in the module root.
```

---

## 2. Models

### 2.1 `workflow.diagram.asset`

**File**: `models/workflow_diagram_asset.py`
**Description**: Canonical BPMN XML source and metadata fingerprint.
**DFR**: `DFR-03-003`, `DFR-03-005`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `definition_version_id` | `Many2one('workflow.definition.version')` | Yes | — | Yes | Yes | `Version` | — | `ondelete='cascade'`; one-to-one relationship |
| `bpmn_xml` | `Text` | No | — | — | — | `BPMN XML` | `Canonical BPMN 2.0 XML` | Updated via modeler; main source of truth |
| `bpmn_hash` | `Char(64)` | No | — | Yes | Yes | `BPMN Hash` | `SHA-256 of canonical XML` | Recomputed on save |
| `last_edited_by_id` | `Many2one('res.users')` | No | — | — | Yes | `Last Edited By` | — | — |
| `last_edited_at_utc` | `Datetime` | No | — | — | Yes | `Last Edited At` | — | — |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='definition_version_id.company_id'`, `store=True` |

**Business Methods**:

| Method | Parameters | Returns | DFR |
|---|---|---|---|
| `save_bpmn_xml` | `bpmn_xml, user_id` | `self` | `DFR-03-003` |
| `import_bpmn_xml` | `xml_payload` | `self` | `DFR-03-005` |
| `export_bpmn_xml` | — | `str` (XML) | `DFR-03-005` |
| `_compute_bpmn_hash` | `bpmn_xml` | `str` (SHA-256) | `DFR-03-003` |

---

### 2.2 `workflow.diagram.validation.result`

**File**: `models/workflow_diagram_validation_result.py`
**Description**: Structured validation errors and warnings per element.
**DFR**: `DFR-03-006`

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|
| `definition_version_id` | `Many2one('workflow.definition.version')` | Yes | — | Yes | Yes | `Version` | — | `ondelete='cascade'` |
| `element_id` | `Char(64)` | Yes | — | — | Yes | `Element ID` | `BPMN element ID` | — |
| `element_type` | `Char(64)` | Yes | — | — | Yes | `Element Type` | `BPMN element type` | — |
| `xpath_location` | `Char(255)` | No | — | — | Yes | `XPath` | — | — |
| `error_category` | `Selection` | Yes | — | — | Yes | `Category` | — | `structural`, `semantic`, `unsupported_element`, `reference_resolution` |
| `error_code` | `Char(64)` | Yes | — | — | Yes | `Error Code` | — | Machine-readable |
| `severity` | `Selection` | Yes | `error` | — | Yes | `Severity` | — | `error`, `warning` |
| `remediation_hint` | `Text` | No | — | — | Yes | `Remediation` | — | Human-readable fix suggestion |
| `validated_at_utc` | `Datetime` | — | `fields.Datetime.now` | — | Yes | `Validated At` | — | — |
| `company_id` | `Many2one('res.company')` | — | — | Yes | Yes | `Company` | — | `related='definition_version_id.company_id'`, `store=True` |

---

## 3. OWL Components

### 3.1 BPMN Modeler Component

**File**: `static/src/components/bpmn_modeler/bpmn_modeler.js`
**Template**: `static/src/components/bpmn_modeler/bpmn_modeler.xml`
**Styles**: `static/src/components/bpmn_modeler/bpmn_modeler.scss`

**Component Name**: `BpmnModeler`
**Registry**: `@web/core/registry` → field registry as `bpmn_modeler`

**Props**:

| Prop | Type | Required | Description |
|---|---|---|---|
| `record` | `Object` | Yes | OWL form record |
| `name` | `String` | Yes | Field name containing BPMN XML |
| `readonly` | `Boolean` | No | If true, disables editing |

**Lifecycle**:

1. `setup()` — register modeler container ref.
2. `onMounted()` — lazy-load bpmn-js library, initialize `BpmnModeler` instance, import XML from `record.data[name]`.
3. On XML change (modeler event) → debounce 500ms → call `record.update({ [name]: xml })`.
4. `onWillUnmount()` — destroy modeler instance to prevent memory leaks.

**Key Behaviors**:

| Behavior | Implementation |
|---|---|
| Lazy load | Import bpmn-js only when component mounts (ADR-003) |
| Palette | Show only supported elements: start event, end event, user task, exclusive gateway, parallel gateway, timer event, sequence flow |
| Property panel | Inline panel for element name, condition expression, timer configuration |
| Save | Debounced XML extraction via `modeler.saveXML()` → update record field |
| Validation trigger | On save, call RPC `validate_bpmn_xml` and display errors inline |
| Readonly mode | Use `BpmnViewer` instead of `BpmnModeler` when `readonly=true` |

**Events Emitted:**

| Event | Payload | When |
|---|---|---|
| `bpmn:save` | `{ xml: String }` | After debounced XML extraction completes |
| `bpmn:validate` | `{ errors: Array, warnings: Array }` | After RPC validation call returns |
| `bpmn:element-click` | `{ elementId: String, elementType: String }` | User clicks a BPMN element |
| `bpmn:dirty` | `{ isDirty: Boolean }` | Diagram modified without save |

**RPC Methods Called:**

| Method | Model | Parameters | Returns | When |
|---|---|---|---|---|
| `validate_bpmn_xml` | `workflow.diagram.asset` | `{ xml: String }` | `{ valid: Boolean, errors: [...] }` | On save / explicit validate |
| `write` | `workflow.definition.version` | `{ bpmn_xml: String }` | `Boolean` | On save (via `record.update`) |

### 3.2 BPMN Viewer Component

**File**: `static/src/components/bpmn_viewer/bpmn_viewer.js`
**Template**: `static/src/components/bpmn_viewer/bpmn_viewer.xml`
**Styles**: `static/src/components/bpmn_viewer/bpmn_viewer.scss`

**Component Name**: `BpmnViewer`
**Registry**: Field registry as `bpmn_viewer`

**Props**:

| Prop | Type | Required | Description |
|---|---|---|---|
| `bpmnXml` | `String` | Yes | BPMN XML content |
| `overlayData` | `Object` | No | Runtime overlay state |
| `onNodeClick` | `Function` | No | Click handler for nodes |

**Runtime Overlay Contract** (`overlayData` shape):

```json
{
  "nodes": {
    "<node_id>": {
      "state": "active|completed|pending|skipped|timed_out",
      "assignees": ["User Name"],
      "decision": "approve|reject|null"
    }
  },
  "activeTokenPath": ["<node_id_1>", "<node_id_2>"]
}
```

**Visual Rules** (DFR-03-008):

| Node State | Color | Border | Icon |
|---|---|---|---|
| `active` | `#FFB74D` (orange) | 3px solid | Spinner |
| `completed` | `#81C784` (green) | 2px solid | Check |
| `pending` | `#E0E0E0` (gray) | 1px dashed | — |
| `skipped` | `#BDBDBD` (dim gray) | 1px dotted | Slash |
| `timed_out` | `#E57373` (red) | 2px solid | Clock |

**Performance** (NFR-009):

| Metric | Target |
|---|---|
| P95 initial load (≤75 nodes) | < 1.5 seconds |
| Overlay refresh | Incremental (no full reparse) |
| Bundle size | Lazy-loaded, not in main bundle |

### 3.3 BPMN Field Widget

**File**: `static/src/fields/bpmn_field.js`

**Purpose**: Register a custom OWL field widget `bpmn_xml` that renders `BpmnModeler` in edit mode and `BpmnViewer` in readonly mode.

```javascript
// Pseudocode
registry.category("fields").add("bpmn_xml", {
    component: BpmnFieldComponent,
    supportedTypes: ["text"],
});
```

---

## 4. Views

### 4.1 Diagram Views (Definition Version Extension)

**File**: `views/workflow_diagram_views.xml`

Extend `workflow.definition.version` form view from `dynamic_approval_core` to add BPMN editor tab:

```xml
<record id="view_workflow_version_form_bpmn" model="ir.ui.view">
    <field name="name">workflow.definition.version.form.bpmn</field>
    <field name="model">workflow.definition.version</field>
    <field name="inherit_id" ref="dynamic_approval_core.view_workflow_version_form"/>
    <field name="arch" type="xml">
        <xpath expr="//notebook" position="inside">
            <page string="BPMN Diagram" name="bpmn_diagram">
                <field name="bpmn_xml" widget="bpmn_xml"
                       invisible="not diagram_asset_id"/>
            </page>
        </xpath>
    </field>
</record>
```

### 4.2 Validation Result Views

List view for validation results (inline in version form or standalone):

**XML ID**: `view_workflow_validation_result_list`

| Column | Widget |
|---|---|
| `element_id` | — |
| `element_type` | — |
| `error_category` | `badge` |
| `severity` | `badge` (decoration-danger for error, decoration-warning for warning) |
| `error_code` | — |
| `remediation_hint` | — |

---

## 5. Security

### 5.1 Access Rights (`security/ir.model.access.csv`)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_diagram_asset_designer,workflow.diagram.asset designer,model_workflow_diagram_asset,dynamic_approval_core.group_workflow_designer,1,1,1,1
access_diagram_asset_admin,workflow.diagram.asset admin,model_workflow_diagram_asset,dynamic_approval_core.group_workflow_admin,1,1,1,1
access_diagram_asset_approver,workflow.diagram.asset approver,model_workflow_diagram_asset,dynamic_approval_core.group_workflow_approver,1,0,0,0
access_diagram_asset_auditor,workflow.diagram.asset auditor,model_workflow_diagram_asset,dynamic_approval_core.group_workflow_auditor,1,0,0,0
access_validation_result_designer,workflow.diagram.validation.result designer,model_workflow_diagram_validation_result,dynamic_approval_core.group_workflow_designer,1,0,0,0
access_validation_result_admin,workflow.diagram.validation.result admin,model_workflow_diagram_validation_result,dynamic_approval_core.group_workflow_admin,1,1,1,1
access_validation_result_auditor,workflow.diagram.validation.result auditor,model_workflow_diagram_validation_result,dynamic_approval_core.group_workflow_auditor,1,0,0,0
```

### 5.2 Record Rules

| XML ID | Model | Domain | Global |
|---|---|---|---|
| `rule_diagram_asset_company` | `workflow.diagram.asset` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes |
| `rule_validation_result_company` | `workflow.diagram.validation.result` | `['|',('company_id','=',False),('company_id','in',company_ids)]` | Yes |

---

## 6. File Structure

```
dynamic_approval_bpmn/
├── __init__.py
├── __manifest__.py
├── readme/
│   ├── DESCRIPTION.rst
│   └── CONTRIBUTORS.rst
├── models/
│   ├── __init__.py
│   ├── workflow_diagram_asset.py
│   └── workflow_diagram_validation_result.py
├── views/
│   ├── workflow_diagram_views.xml
│   └── menu_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── workflow_bpmn_security.xml
├── static/
│   ├── lib/
│   │   └── bpmn-js/
│   │       └── bpmn-modeler.production.min.js
│   ├── src/
│   │   ├── components/
│   │   │   ├── bpmn_modeler/
│   │   │   │   ├── bpmn_modeler.js
│   │   │   │   ├── bpmn_modeler.xml
│   │   │   │   └── bpmn_modeler.scss
│   │   │   └── bpmn_viewer/
│   │   │       ├── bpmn_viewer.js
│   │   │       ├── bpmn_viewer.xml
│   │   │       └── bpmn_viewer.scss
│   │   └── fields/
│   │       └── bpmn_field.js
│   └── description/
│       └── icon.png
└── tests/
    ├── __init__.py
    └── test_bpmn_validation.py
```

---

## 7. Supported BPMN Element Subset

| BPMN Element | Internal Type Key | Modeler Palette | Runtime Engine |
|---|---|---|---|
| Start Event | `start_event` | Yes | Yes |
| End Event | `end_event` | Yes | Yes |
| User Task | `user_task` | Yes | Yes |
| Exclusive Gateway | `exclusive_gateway` | Yes | Yes |
| Parallel Gateway | `parallel_gateway` | Yes | Yes |
| Intermediate Timer Event | `timer_event` | Yes | Yes |
| Sequence Flow | — | Yes | Yes |
| All other elements | — | **No** (blocked by palette) | **No** (fail validation `DFR-03-006`) |
