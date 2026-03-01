Dynamic Approval Workflow — Core
=================================

Configurable, multi-step approval workflow engine for Odoo 19.

This module provides the core runtime for dynamic approval workflows
that can be bound to any Odoo model and action through UI configuration,
without per-model code changes.

**Key capabilities:**

* Workflow definition, versioning, and publishing lifecycle.
* Binding workflows to model/action pairs via configuration.
* ORM-level gate enforcement (``orm_enforced``, ``hybrid``, ``ui_only``).
* Runtime orchestration with sequential, parallel, and conditional paths.
* Dynamic approver resolution (users, groups, roles, hierarchy, delegates, quorum).
* Human-task lifecycle: approve, reject, request-change, delegate, escalate.
* SLA deadlines and timer-based escalation policies.
* Digital signature evidence capture and attestation.
* Temporary access-grant management with automatic revocation.
* Notification framework (in-app, email) with configurable templates.
* Signed webhook event dispatch with retry and dead-letter handling.
* Idempotency registry for at-most-once mutation semantics.
* Incident management for runtime/configuration errors.
* Full immutable audit trail with correlation-based tracing.

Architecture reference: ``ADR-001 — Three-Module Architecture``.
