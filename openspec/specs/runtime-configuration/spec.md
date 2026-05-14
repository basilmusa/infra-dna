## Purpose

Define the expected behavior for loading and validating top-level runtime configuration used by infra-dna CLI workflows.

## Requirements

### Requirement: Project loads runtime Neo4j settings from a dedicated top-level config file
The system SHALL support a dedicated top-level runtime configuration file for Neo4j connection settings. The supported default config file name SHALL be `infra-dna.toml`, located at the project root or explicitly selected through the CLI. The runtime config format MUST be separate from package metadata.

#### Scenario: Default config file is used for normal CLI load mode
- **WHEN** a user runs `infra-dna` without `--validate-only` and without a config override
- **THEN** the system loads Neo4j runtime settings from the default `infra-dna.toml` file

#### Scenario: Explicit config file override is honored
- **WHEN** a user runs `infra-dna` with a `--config` path
- **THEN** the system loads Neo4j runtime settings from the specified configuration file instead of the default path

### Requirement: Configuration service validates required Neo4j settings
The system SHALL provide a dedicated configuration service that reads and validates the runtime configuration file before Neo4j load mode begins. The configuration service MUST require a Neo4j `uri`, `username`, and `password`, and it MUST treat `database` as optional.

#### Scenario: Valid Neo4j configuration is returned as typed application config
- **WHEN** the configuration file contains the required Neo4j settings with valid string values
- **THEN** the configuration service returns typed application configuration that can be used to construct Neo4j loading components

#### Scenario: Missing required Neo4j setting is rejected
- **WHEN** the configuration file omits a required Neo4j setting such as `uri`, `username`, or `password`
- **THEN** the configuration service reports a configuration error and the CLI does not begin Neo4j loading

#### Scenario: Invalid config value type is rejected
- **WHEN** a required Neo4j setting has the wrong type
- **THEN** the configuration service reports a configuration error and the CLI does not begin Neo4j loading

### Requirement: Project provides an example config file and excludes local config from git
The system SHALL provide a checked-in example runtime configuration file for Neo4j setup and SHALL exclude the local runtime configuration file from git tracking. Project documentation MUST explain how to copy the example file into a local `infra-dna.toml` and fill in Neo4j connection settings before running load mode.

#### Scenario: Repository includes an example config template
- **WHEN** a developer inspects the project root
- **THEN** the repository includes an example runtime config file that documents the expected Neo4j config keys

#### Scenario: Local runtime config is git-ignored
- **WHEN** a developer creates a local `infra-dna.toml`
- **THEN** the repository gitignore rules exclude that file from normal version control tracking

#### Scenario: Documentation explains copy-and-configure flow
- **WHEN** a developer follows the project README for Neo4j loading setup
- **THEN** the documentation instructs the developer to copy the example config file to `infra-dna.toml` and update it with local Neo4j settings
