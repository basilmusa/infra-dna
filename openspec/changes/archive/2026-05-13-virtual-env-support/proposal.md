## Why

The project needs a consistent Python environment so required dependencies such as the Neo4j driver are installed and used predictably instead of relying on whatever is present globally. The current CLI naming and setup guidance also need to be tightened so the project is easier to install, run, and document as a real Python application.

## What Changes

- Add a documented, first-class local virtual environment workflow using a repo-local `.venv`.
- Treat the Neo4j Python driver as a required project dependency.
- Standardize the recommended installation workflow around installing the project into the virtual environment for development.
- Rename the CLI command from `infra-dna-parse` to `infra-dna`.
- Update project documentation and setup guidance to reflect Python project best practices and the new CLI name.

## Capabilities

### New Capabilities
- `python-environment-setup`: Defines the required Python environment, dependency installation flow, and local virtual environment workflow for developing and running the project.

### Modified Capabilities
- `yaml-graph-parser`: Update the parser CLI contract and documentation to use the `infra-dna` command name and the project-managed Python environment.

## Impact

Affected areas include Python packaging, project dependencies, CLI entrypoints, developer setup instructions, and the runtime foundation needed for Neo4j-backed import work.
