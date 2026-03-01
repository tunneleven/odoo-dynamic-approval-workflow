# ADR-003: bpmn-js as OWL 2 Components with Lazy Loading

**Status:** Accepted  
**Date:** 2026-03-01  
**Decision Makers:** Tech Lead  
**SDS Reference:** §5 BPMN Integration Architecture

---

## Context

The SRS mandates `bpmn-js` for diagram design and viewing (Parent SRS §5.3). The integration question is how to embed bpmn-js within Odoo 19's OWL 2 frontend framework, and when to load the library.

Options considered:

1. **Eager loading** — bundle bpmn-js into main web assets. Loaded for every user on every page.
2. **Lazy loading via OWL component** — load bpmn-js on-demand when modeler/viewer is first mounted.
3. **iframe isolation** — run bpmn-js in a sandboxed iframe.

## Decision

**Option 2: bpmn-js as OWL 2 components with lazy loading.**

Two OWL components (`BpmnModeler`, `BpmnViewer`) load the bpmn-js library on-demand via `loadJS()` in their `onWillStart` lifecycle hook. The library is bundled in a dedicated asset bundle `dynamic_approval_bpmn.bpmn_assets`, separate from the main web backend bundle.

## Rationale

### Why lazy loading?

- bpmn-js (modeler build) is ~2MB uncompressed. Eager loading adds this to every page load for every user — unacceptable for the ~90% of users who never open the diagram designer.
- NFR-009 requires < 1.5s diagram viewer load time. Lazy loading on first mount means the library is cached after first use, and subsequent loads hit browser cache.

### Why OWL components (not iframe)?

- OWL components can directly emit events to parent Odoo components (form views, RPC handlers).
- No cross-origin communication overhead.
- SCSS styling integrates with Odoo's theme system (scoped via `.o_daw_` prefix).
- Odoo's OWL lifecycle (`onWillStart`, `onMounted`, `onWillUnmount`) maps naturally to bpmn-js canvas creation/destruction.

### Why not a custom Odoo field widget?

The components ARE registered as field widgets (`bpmn_field.js`) for embedding in form views, but the underlying implementation uses standalone OWL components. This gives flexibility to use them outside form views (e.g., in standalone dashboards or popups).

## Implementation Contract

### Component Architecture

| Component | bpmn-js Mode | Purpose | Key Events |
|---|---|---|---|
| `BpmnModeler` | `Modeler` (full editing) | Design workflows with palette, property panel | `xml.changed`, `element.selected`, `validation.requested` |
| `BpmnViewer` | `NavigatedViewer` (read-only) | View running instances with runtime overlays | `overlay.update`, `node.clicked` |

### Asset Loading Sequence

```
OWL Component mounted
  → onWillStart: loadJS('dynamic_approval_bpmn.bpmn_assets')
  → onMounted: new BpmnModeler({container: this.el}) or new NavigatedViewer(...)
  → Canvas ready
  → importXML(canonical_bpmn_xml)
  → Diagram rendered
```

### Bundle Location

```
dynamic_approval_bpmn/
  static/
    lib/bpmn-js/          # Pre-built bpmn-js distribution (vendor)
    src/components/
      bpmn_modeler/       # OWL modeler component
      bpmn_viewer/        # OWL viewer component
    src/fields/
      bpmn_field.js       # Form field widget registration
```

### Overlay Strategy

- Runtime state displayed via bpmn-js overlay API — no SVG re-import.
- State polling: 5-second interval when viewer is visible.
- CSS classes: `o_daw_node_active`, `o_daw_node_completed`, `o_daw_node_pending`, `o_daw_node_error`.
- Tooltip data bound to overlay elements for approver info and timestamps.

### Supported BPMN Subset

Start event, End event, User task, Exclusive gateway, Parallel gateway, Intermediate timer event, Sequence flow.

Non-supported elements are rejected at import/validation time with structured error messages.

## Consequences

### Positive
- No page load penalty for non-designer users.
- Clean OWL lifecycle management (no orphan canvas instances).
- Theme-consistent styling via scoped SCSS.
- Overlay updates are incremental — no full diagram re-parse for runtime state changes.

### Negative
- First-time load of modeler/viewer has a ~500ms delay for library fetch (mitigated by browser cache on subsequent loads).
- bpmn-js version must be pinned and manually updated in `static/lib/` — no package manager integration.
- Testing OWL + bpmn-js interaction requires browser-based test infrastructure (QUnit/Hoot).

### Mitigation
- Pin bpmn-js version in `__manifest__.py` comments and document upgrade procedure.
- Pre-warm library cache via `prefetch` link tag on workflow management pages.
- OWL component tests mock bpmn-js API for unit tests; full integration tests use Hoot.

## Alternatives Considered

| Option | UX Impact | Complexity | Performance | Verdict |
|---|---|---|---|---|
| Eager loading | None | Low | Bad (2MB on every page) | Rejected |
| Lazy OWL | Minor (first-load delay) | Medium | Good | **Accepted** |
| iframe | Noticeable (cross-origin delay) | High | Medium | Rejected |

## References

- Parent SRS §5.3 (bpmn-js mandatory)
- SRS-03 §6 (supported BPMN subset)
- SRS-03 §8 (canonical XML contract)
- SRS-03 §9.2 (overlay semantics)
- NFR-009 (< 1.5s viewer load)
- Odoo 19 OWL 2 documentation
