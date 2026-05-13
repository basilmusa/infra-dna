## ADDED Requirements

### Requirement: Project supports a standard repo-local virtual environment workflow
The system SHALL define a supported local development workflow based on a repo-local virtual environment named `.venv` created with Python's standard `venv` module. The documented setup flow MUST install the project into that environment before normal CLI usage.

#### Scenario: Developer creates the supported environment
- **WHEN** a developer follows the documented local setup instructions
- **THEN** the instructions create a repo-local `.venv` virtual environment as the supported execution environment

#### Scenario: Developer installs the project into the environment
- **WHEN** a developer completes the documented install flow inside the activated virtual environment
- **THEN** the project is installed into that environment using the project package metadata

### Requirement: Project installs required runtime dependencies through package metadata
The system SHALL declare required runtime dependencies in project package metadata so a standard project install brings in all dependencies needed for supported CLI behavior, including the Neo4j Python driver.

#### Scenario: Standard install includes required dependencies
- **WHEN** a developer installs the project using the documented package install command
- **THEN** the installation includes the dependencies required for the supported CLI workflow, including the Neo4j Python driver

### Requirement: Project documents editable install for development
The system SHALL document editable install as the supported development installation workflow for local contributors.

#### Scenario: Developer follows supported development install
- **WHEN** a developer follows the documented development install workflow
- **THEN** the instructions use an editable project install so local source changes are reflected without reinstalling the package
