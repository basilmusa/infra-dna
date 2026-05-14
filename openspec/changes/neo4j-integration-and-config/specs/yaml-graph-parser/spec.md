## MODIFIED Requirements

### Requirement: Parser dispatches validated records to pluggable consumers
The system SHALL expose entities and relations as canonical parsed records to pluggable consumer callbacks or classes. The parser MUST support consumers such as console printing and Neo4j loading without requiring those consumers to re-parse YAML documents. The consumer contract SHALL include lifecycle hooks for `on_start()` and `on_finish()`. The parser MUST support a workflow in which validation completes before any consumer lifecycle or record dispatch begins, and it MUST allow valid parsed records to be dispatched only after a higher-level caller decides to proceed.

#### Scenario: Consumer lifecycle starts before record dispatch
- **WHEN** a higher-level caller begins dispatching a valid parse result to configured consumers
- **THEN** the parser dispatch flow invokes each consumer’s `on_start()` before dispatching any entity records or relation records

#### Scenario: Consumer receives parsed entities
- **WHEN** the parser dispatches a successfully validated entity record
- **THEN** it dispatches that entity to the configured consumer interface

#### Scenario: Consumer receives parsed relations
- **WHEN** the parser dispatches a successfully validated relation record
- **THEN** it dispatches that relation to the configured consumer interface

#### Scenario: Consumer lifecycle finishes after record dispatch
- **WHEN** the parser completes dispatching all validated entity and relation records to configured consumers
- **THEN** it invokes each consumer’s `on_finish()`

#### Scenario: Invalid parse result does not trigger consumer lifecycle
- **WHEN** the parser has collected one or more validation errors
- **THEN** it does not invoke `on_start()`, `on_entity()`, `on_relation()`, or `on_finish()` for configured consumers

#### Scenario: Valid parse result can be inspected before dispatch decision
- **WHEN** a higher-level caller requests parsing for a workflow that needs post-validation decisions
- **THEN** the parser returns the valid parse result without requiring immediate consumer dispatch

### Requirement: Parser CLI is exposed as infra-dna
The system SHALL expose the installed parser CLI through the `infra-dna` command name as the primary user-facing executable for project workflows. The CLI SHALL support validation-only execution, explicit runtime config selection, and explicit confirmation bypass for destructive Neo4j load mode.

#### Scenario: Installed CLI uses the new command name
- **WHEN** the project is installed through the supported package workflow
- **THEN** the primary installed console command is `infra-dna`

#### Scenario: CLI supports validation-only mode
- **WHEN** a user runs `infra-dna --validate-only`
- **THEN** the CLI validates YAML and exits without prompting for Neo4j load confirmation or starting Neo4j loading

#### Scenario: CLI supports config file override
- **WHEN** a user runs `infra-dna --config <path>`
- **THEN** the CLI uses the specified runtime configuration file for Neo4j load mode

#### Scenario: CLI supports destructive-load confirmation bypass
- **WHEN** a user runs `infra-dna --force`
- **THEN** the CLI bypasses the interactive Neo4j load confirmation prompt after successful validation

### Requirement: Parser remains executable as a Python module
The system SHALL continue to support direct module execution through `python -m infra_dna.cli` in addition to the installed `infra-dna` console command.

#### Scenario: Module execution remains supported
- **WHEN** a user runs `python -m infra_dna.cli` from a correctly configured project environment
- **THEN** the parser CLI executes successfully without requiring the installed console script name
