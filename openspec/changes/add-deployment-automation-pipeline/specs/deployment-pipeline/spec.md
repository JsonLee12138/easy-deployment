## ADDED Requirements
### Requirement: Conditional Configuration Validation Gate
The system SHALL validate deployment configuration only for stages that require configuration input.

#### Scenario: Stage requires configuration
- **WHEN** a user runs a stage that needs configuration (for example deploy, compose push, or remote deploy)
- **THEN** the system validates configuration and blocks execution on validation failure

#### Scenario: Stage does not require configuration
- **WHEN** a user runs a stage that does not depend on deployment configuration
- **THEN** the system does not enforce configuration validation for that stage

### Requirement: Deployment Configuration Creation
The system SHALL create deployment-ready configuration artifacts after validation succeeds.

#### Scenario: Create configuration artifacts
- **WHEN** a user runs the configuration creation stage for a config-dependent flow
- **THEN** the system generates normalized, environment-specific deployment artifacts

### Requirement: Version Default and Policy
The system SHALL support `latest` as default version when version input is omitted.

#### Scenario: Version omitted
- **WHEN** a user runs deployment without passing version explicitly
- **THEN** the system sets version to `latest`

#### Scenario: Version explicitly provided
- **WHEN** a user passes a version value
- **THEN** the system uses the provided version as deployment version

### Requirement: Deployment Execution
The system SHALL execute deployment using generated artifacts and support dry-run mode.

#### Scenario: Dry-run execution
- **WHEN** a user runs deployment with dry-run enabled
- **THEN** the system outputs planned actions without modifying target environments

#### Scenario: Real deployment execution
- **WHEN** a user runs deployment without dry-run and with successful required validations
- **THEN** the system executes deployment and records stage-level status

### Requirement: Post-Deployment Verification and Rollback
The system SHALL perform post-deployment health checks and trigger rollback if health criteria are not met.

#### Scenario: Health checks pass
- **WHEN** post-deployment checks meet defined service thresholds
- **THEN** the system marks deployment as successful

#### Scenario: Health checks fail
- **WHEN** post-deployment checks exceed failure thresholds within retry bounds
- **THEN** the system triggers rollback and records rollback outcomes

### Requirement: Deployment Audit Logging
The system SHALL emit audit logs for validation, config creation, deployment execution, and rollback actions.

#### Scenario: Audit record emitted per stage
- **WHEN** any deployment stage starts or completes
- **THEN** the system writes structured audit entries with timestamp, actor, environment, and result
