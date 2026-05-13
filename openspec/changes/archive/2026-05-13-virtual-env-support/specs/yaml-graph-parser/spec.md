## ADDED Requirements

### Requirement: Parser CLI is exposed as infra-dna
The system SHALL expose the installed parser CLI through the `infra-dna` command name as the primary user-facing executable for project workflows.

#### Scenario: Installed CLI uses the new command name
- **WHEN** the project is installed through the supported package workflow
- **THEN** the primary installed console command is `infra-dna`

### Requirement: Parser documentation uses the project-managed Python environment
The system SHALL document parser setup and invocation in terms of the supported project-managed Python environment rather than assuming globally installed dependencies.

#### Scenario: CLI usage examples assume the supported environment
- **WHEN** the project documentation shows setup or invocation examples for the parser CLI
- **THEN** those examples reference the supported virtual environment workflow and the `infra-dna` command

### Requirement: Parser remains executable as a Python module
The system SHALL continue to support direct module execution through `python -m infra_dna.cli` in addition to the installed `infra-dna` console command.

#### Scenario: Module execution remains supported
- **WHEN** a user runs `python -m infra_dna.cli` from a correctly configured project environment
- **THEN** the parser CLI executes successfully without requiring the installed console script name
