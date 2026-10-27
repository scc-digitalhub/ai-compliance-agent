# compliance_core

Framework-neutral compliance contracts, validation, OKF/OKB knowledge access, workspace state,
analysis services, and the canonical tool catalog. This package has no Google ADK dependency.

The knowledge bundle is included as package data. Set `OKF_PATH` to use an alternate bundle and
`COMPLIANCE_WORKSPACE` to select the default workspace for state operations.

This import package is included in the unified `ai-compliance-platform` distribution. The base
installation provides the core dependencies; runtime adapters are selected with distribution extras.
