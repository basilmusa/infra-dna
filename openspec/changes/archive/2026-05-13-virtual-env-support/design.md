## Context

The project currently provides a Python CLI and library package with a minimal dependency set and a console script named `infra-dna-parse`. The next phase of the project requires the Neo4j Python driver as part of normal project setup, which raises the cost of relying on globally installed packages or ad hoc local environments. The project also needs a clearer user-facing CLI identity, so the installation and execution path should be simplified around a single `infra-dna` command and a documented repo-local virtual environment workflow.

This change is cross-cutting because it affects packaging, dependency installation, the CLI entrypoint, documentation, and local development conventions. It also establishes the runtime baseline for future Neo4j-backed import work.

## Goals / Non-Goals

**Goals:**
- Define a standard repo-local `.venv` workflow for developing and running the project.
- Make the Neo4j Python driver a required dependency installed through the project package metadata.
- Rename the console script from `infra-dna-parse` to `infra-dna`.
- Update project documentation so contributors use a consistent setup flow, including editable installs for development.
- Keep the project runnable both through the installed console script and `python -m` module execution.

**Non-Goals:**
- Implement Neo4j loading behavior in this change.
- Introduce multiple environment managers or support matrices for tools such as Poetry, Pipenv, or Conda.
- Containerize the development workflow.
- Change the parser data model or validation behavior beyond any CLI naming references required by the rename.

## Decisions

### Use a repo-local `.venv` as the documented standard

The project will standardize on a repo-local virtual environment named `.venv` created with the standard library `venv` module.

Rationale:
- `venv` is built into Python and does not add an extra bootstrap dependency.
- `.venv` is a familiar convention and fits well with existing editor tooling.
- A single documented workflow is easier to support than multiple equivalent setup paths.

Alternatives considered:
- Global Python environment: rejected because it makes dependency state unpredictable and complicates Neo4j driver setup.
- Third-party environment managers like Poetry or Pipenv: rejected for now because they add workflow and tooling overhead without solving a current project-specific problem.
- `uv`: viable, but rejected as the primary documented path because it introduces another required tool. It can remain compatible as an unofficial choice if someone prefers it.

### Treat `neo4j` as a required dependency

The Neo4j Python driver will be added to the main project dependency list in `pyproject.toml`.

Rationale:
- Neo4j support is intended to be part of the normal project capability, not an optional extension.
- Requiring the dependency keeps installation and documentation simple.
- It avoids branching logic in documentation and setup commands.

Alternatives considered:
- Optional dependency extra: rejected because it creates two setup paths and weakens the “one standard environment” goal.

### Keep editable install as the recommended development install

The documented install command will remain `pip install -e .` inside the activated virtual environment.

Rationale:
- Editable installs are the most practical fit for active local development.
- They provide the console script entrypoint while using the working tree directly.
- They align with the current package-based CLI setup.

Alternatives considered:
- Running only `python -m infra_dna.cli`: rejected as the primary workflow because it does not install dependencies or console scripts and depends more on the current working directory.
- Non-editable install: rejected for development because it requires reinstalling after local code changes.

### Rename the console script to `infra-dna`

The project’s installed CLI command will be renamed from `infra-dna-parse` to `infra-dna`.

Rationale:
- The shorter command reads as the project’s primary interface instead of one subcommand-shaped tool.
- It leaves room for future expansion without renaming the installed executable again.
- It better matches the repository and package identity.

Alternatives considered:
- Keep `infra-dna-parse`: rejected because it over-specifies the current parser behavior and is less suitable as the long-term project command.
- Ship both names permanently: rejected because it adds maintenance surface and documentation ambiguity.

### Preserve module execution as a secondary entrypoint

The project should continue to support `python -m infra_dna.cli` for direct execution, even though the primary documented command will be `infra-dna`.

Rationale:
- It is useful for debugging and environments where the console script is not yet on `PATH`.
- It costs very little to preserve.

## Risks / Trade-offs

- [Developers already using a different environment layout] → Document the `.venv` workflow clearly and treat it as the supported path without trying to block personal alternatives.
- [CLI rename breaks old usage habits] → Update README examples and developer instructions consistently. Decide whether to provide a short compatibility period or do a direct rename.
- [Required Neo4j dependency increases install surface] → Accept the larger dependency footprint in exchange for one consistent installation flow.
- [Platform-specific activation steps can confuse users] → Document activation commands carefully and keep the rest of the workflow identical after activation.

## Migration Plan

1. Update `pyproject.toml` to require the Neo4j driver and rename the console script to `infra-dna`.
2. Ensure `.gitignore` continues to cover `.venv/` and other local environment artifacts.
3. Update `README.md` with the supported setup flow:
   - create `.venv`
   - activate it
   - run `pip install -e .`
   - invoke `infra-dna`
4. Update any tests or documentation that reference `infra-dna-parse`.
5. Verify that the CLI still works through both `infra-dna` and `python -m infra_dna.cli`.

Rollback strategy:
- Revert the console script rename in `pyproject.toml`.
- Remove the `neo4j` dependency from required dependencies if the project decides not to make it mandatory.
- Restore prior README command examples.

## Open Questions

- Should the old `infra-dna-parse` command remain temporarily as a compatibility alias, or should the rename be immediate?
- Do we want README setup instructions for both Unix-like shells and Windows, or only the primary development platform for now?
