Dynamic Approval Workflow — Operations
=======================================

Operational monitoring, retention policies, and archival/purge
tools for the Dynamic Approval Workflow suite.

**Key capabilities:**

* Operations dashboard with instance/task/incident metrics.
* Retention policy profiles: ``short_term`` (90 d), ``standard``
  (365 d), ``compliance_extended`` (7 y).
* Archival cron job for terminal instances past retention window.
* Operator-triggered purge with legal-hold awareness.
* SLO tracking and traceability reporting.
* Immutable audit evidence for all archival/purge operations.

Install this module for production environments that require
monitoring and data lifecycle management.
``dynamic_approval_core`` runs independently without this module.

Architecture reference: ``ADR-001``.
