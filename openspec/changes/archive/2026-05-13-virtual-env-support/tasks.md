## 1. Packaging And Environment Setup

- [x] 1.1 Add the required `neo4j` dependency to `pyproject.toml`.
- [x] 1.2 Rename the console script entrypoint in `pyproject.toml` from `infra-dna-parse` to `infra-dna`.
- [x] 1.3 Verify `.gitignore` covers `.venv/` and any related local Python environment artifacts expected by the supported workflow.

## 2. CLI And Documentation Updates

- [x] 2.1 Update project documentation to define the supported repo-local `.venv` workflow, including environment creation, activation, and `pip install -e .`.
- [x] 2.2 Update README command examples and CLI references to use `infra-dna` as the primary installed command.
- [x] 2.3 Preserve and document `python -m infra_dna.cli` as a supported secondary execution path.

## 3. Verification

- [x] 3.1 Update tests or test fixtures that reference the old `infra-dna-parse` command name, if any.
- [x] 3.2 Verify the project installs successfully in a fresh `.venv` with required dependencies.
- [x] 3.3 Verify the CLI runs successfully through both `infra-dna` and `python -m infra_dna.cli` from the supported project environment.
