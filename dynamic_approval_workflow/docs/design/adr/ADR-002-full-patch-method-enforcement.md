# ADR-002: Full `_patch_method` Enforcement for All Bound Models

**Status:** Accepted  
**Date:** 2026-03-01  
**Decision Makers:** Tech Lead, Security Lead  
**SDS Reference:** §7 ORM Interceptor Design

---

## Context

The SRS requires a generic ORM enforcement interceptor that gates business method execution based on workflow binding configuration. Three enforcement coverage strategies were evaluated:

1. **Phase 1 only** — `call_kw` controller interception + UI hook. Misses direct Python calls.
2. **Phase 1+2** — `call_kw` interception + selective `_patch_method` for high-risk models.
3. **Full `_patch_method`** — every bound model+method pair wrapped at registry load time.

The SRS brainstorm document (supplementary/brainstorm_orm_enforcement_without_model_changes.md) recommended Option C (Hybrid Risk-Tier), which maps to a phased approach. However, the stakeholder decision prioritizes security coverage completeness over implementation phasing.

## Decision

**Option 3: Full `_patch_method` for all bound models from day one.**

Every model+method pair with an active `orm_enforced` or `hybrid` binding is wrapped via `cls._patch_method()` at registry load/update time. No phased rollout.

## Rationale

### Why full coverage from day one?

1. **No enforcement gaps**: `call_kw`-only interception misses direct Python calls within server code (automated actions, in-process method calls). `_patch_method` wraps the method on the model class itself, covering all call paths including `sudo()`.
2. **Compliance requirement**: SRS-02 §7.2 Channel Coverage Matrix requires `orm_enforced` to cover Form, JSON-RPC, import, server actions, cron, and `sudo()`. Only `_patch_method` achieves this without custom middleware per channel.
3. **No security debt**: A phased approach creates a window where some bound models are only partially enforced. For `compliance_critical` bindings, this is unacceptable.
4. **Simpler mental model**: One enforcement mechanism, not two. Developers and AI agents don't need to reason about "which models are in phase 1 vs phase 2."

### Why `_patch_method` over alternatives?

| Alternative | Coverage | Drawback |
|---|---|---|
| `call_kw` controller hook | UI + RPC only | Misses internal Python calls, cron, server actions |
| `create/write` override via mixin | CRUD only | Doesn't cover custom business methods like `action_confirm()` |
| BaseModel monkey-patch | Global | Too broad; performance cost on every model call |
| `_patch_method` | Per-method, per-model | Targeted, standard Odoo API, no core modification |

### Performance consideration

`_patch_method` adds one function call overhead per patched method invocation. For workflows with ~50 active bindings, this means ~50 methods have a wrapper. The wrapper evaluates binding lookup (indexed query, cacheable) and gate state. Target overhead: < 5ms per intercepted call.

## Implementation Contract

### Lifecycle

1. **Registry load**: Read active bindings → build `(model, method)` pairs → `_patch_method` each.
2. **Config change**: Increment `interceptor_config_revision` → `registry.signal_changes()` → workers re-apply.
3. **Wrapper**: Check bypass token → resolve binding → evaluate gate → audit log → call original or raise.

### Channel coverage achieved

| Channel | Covered | Why |
|---|---|---|
| Form button | Yes | UI → RPC → patched method |
| JSON/XML-RPC | Yes | RPC → patched method |
| Import | Yes | Import → `create/write` → patched |
| Server actions | Yes | Actions call methods → patched |
| Cron | Yes | Cron calls methods → patched |
| `sudo()` | Yes | Patch is on the class, not the recordset |
| Direct SQL | No | Out of scope — documented limitation |

### Fail-closed

On any interceptor error (binding lookup failure, gate evaluation exception), the action is **blocked** for `orm_enforced` and `hybrid` modes. This is a safety default.

### Bypass

- No client-side bypass flags (SRS-02 §7.6.4).
- Server-side `_workflow_bypass_token` in context — set only by engine internals (callback execution, system actions).
- Every bypass is audit-logged.

## Consequences

### Positive
- Complete channel coverage from initial release.
- Single enforcement mechanism — simpler architecture.
- No "phase 2" migration or security gap window.
- AI agents have one pattern to implement, not conditional logic.

### Negative
- Higher implementation complexity in Phase 1 (must implement `_patch_method` infrastructure before any workflow runs).
- Registry reload on binding config changes may cause brief latency spike for workers picking up new patches.
- Performance testing required to validate < 5ms overhead target under load.

### Mitigation
- Binding lookup result is cached in-process and invalidated by `interceptor_config_revision` change.
- Registry reload is Odoo's standard mechanism — well-tested at scale.
- Performance testing included as explicit Phase 1 acceptance criterion.

## Alternatives Considered

| Option | Coverage | Complexity | Security Gap | Verdict |
|---|---|---|---|---|
| Phase 1 only (`call_kw`) | Partial | Low | Yes | Rejected |
| Phase 1+2 (selective) | Gradual | Medium | Temporary | Rejected |
| Full `_patch_method` | Complete | High | None | **Accepted** |

## References

- SRS-02 §7 (ORM Enforcement Architecture)
- SRS-02 §7.2 (Channel Coverage Matrix)
- SRS-02 §7.5 (`_patch_method` at registry-time)
- Brainstorm: `supplementary/brainstorm_orm_enforcement_without_model_changes.md` §4–7
- Odoo source: `odoo/models.py` — `BaseModel._patch_method()` API
