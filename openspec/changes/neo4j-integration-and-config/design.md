## Context

The codebase already has the core pieces needed for Neo4j loading:

- `GraphParser` validates entity and relation YAML and only dispatches consumers after a clean run
- `Neo4jService` connects to Neo4j and executes Cypher
- `Neo4jVisitorHandler` clears the graph, ensures schema, and loads validated entities and relations

What is missing is the runtime integration path. Today the primary `infra-dna` CLI validates YAML and optionally prints records, but it does not read runtime configuration, it does not instantiate Neo4j loading components, and it does not protect users from unintentionally clearing a target database.

This change needs to preserve the existing safety property that invalid YAML must never trigger destructive Neo4j work, while also making the default CLI behavior load Neo4j after successful validation.

## Goals / Non-Goals

**Goals:**
- Add a dedicated configuration loading component that reads a top-level runtime configuration file and returns typed `AppConfig` and `Neo4jConfig` values for Neo4j loading.
- Make `infra-dna` validate first and then load Neo4j automatically on successful runs.
- Support `--validate-only`, `--config`, and `--force` CLI behavior.
- Warn interactive users before clearing the configured Neo4j database.
- Add an example configuration file, ignore the real local config file in git, and document the setup flow in `README.md`.
- Preserve clean separation between configuration loading, parser validation, and Neo4j loading concerns.

**Non-Goals:**
- Add environment-variable-first configuration discovery or multi-source configuration merging in the first version.
- Change the graph model, Neo4j schema model, or relation loading semantics established by the existing Neo4j support work.
- Introduce a general plugin system for consumers or alternate database backends.
- Support partial graph updates; the intended behavior remains clear-and-rebuild.

## Decisions

### 1. Use a dedicated top-level runtime config file and typed config loader

The runtime configuration will live in a dedicated repo-root file such as `infra-dna.toml`, not in `pyproject.toml`. An `AppConfigLoader` will own locating the file, reading TOML, validating required fields, and returning typed configuration objects such as `AppConfig` and `Neo4jConfig`.

The repository will also include an example configuration file such as `infra-dna.example.toml`. The real `infra-dna.toml` file will be ignored in `.gitignore`, and the documentation will instruct users to copy the example file and fill in local credentials before running the load workflow.

Rationale:
- keeps runtime settings separate from packaging metadata
- gives the CLI a single dependency for configuration loading
- creates a clear place for config validation and error reporting
- provides a safe onboarding path without encouraging committed local credentials

Alternatives considered:
- `pyproject.toml`: rejected because runtime secrets and application settings do not belong in package metadata
- reading config directly in `cli.py`: rejected because it mixes orchestration with parsing and validation of config data

### 2. Split validation from consumer dispatch at the CLI integration boundary

The CLI needs to validate YAML first, then decide whether to proceed with destructive Neo4j loading. To support this cleanly, the parser flow will be adjusted so validation and dispatch can be controlled separately rather than always dispatching during `parse()`.

The intended flow is:

```text
load CLI args
  ↓
optionally load config
  ↓
parse and validate YAML
  ↓
if invalid: print errors and exit
  ↓
if --validate-only: print summary and exit
  ↓
if interactive and not --force: prompt for confirmation
  ↓
dispatch Neo4j visitor
```

Rationale:
- ensures the user is only prompted when validation has already succeeded
- preserves the invariant that invalid runs never trigger Neo4j loading
- makes CLI policy decisions explicit rather than hidden inside parser execution

Alternatives considered:
- prompt before calling `parse()`: rejected because users would confirm a destructive action before knowing whether validation succeeded
- keep automatic dispatch inside `parse()`: rejected because the CLI needs a decision point between successful validation and destructive loading

### 3. Make destructive confirmation a CLI policy, using `--force` for bypass

The confirmation prompt belongs in `cli.py`, not in `GraphParser` or `Neo4jVisitorHandler`. The CLI will prompt only when all of the following are true:

- validation succeeded
- Neo4j loading is enabled
- `--validate-only` is not set
- `--force` is not set
- standard input is interactive

The prompt will clearly state that the configured Neo4j database will have all nodes and relationships removed and then rebuilt from infra-dna YAML.

For non-interactive environments, the CLI will refuse to proceed with destructive loading unless `--force` is provided.

Rationale:
- keeps user interaction policy in the command-line layer
- avoids hidden prompts inside library code
- supports both safe human usage and automation
- uses a clearer destructive-action bypass name than `--yes`

Alternatives considered:
- `--yes`: rejected because it reads like generic agreement rather than explicit destructive intent
- always prompt: rejected because it breaks automation and CI usage
- never prompt: rejected because the default workflow is destructive and needs a human safeguard

### 4. Keep Neo4j loading construction in the CLI

The CLI will instantiate `Neo4jService` and `Neo4jVisitorHandler` after reading runtime configuration and after determining that a load should proceed. Parser, visitor, and service classes will remain configuration-agnostic.

Rationale:
- preserves current layering
- keeps file I/O and runtime policy outside of the Neo4j modules
- makes test boundaries clearer

Alternatives considered:
- have `Neo4jService` read config directly: rejected because it couples database code to file-system concerns
- have the parser instantiate consumers: rejected because parser responsibilities should remain focused on parsing and validation

## Risks / Trade-offs

- [Destructive default behavior] → Mitigation: require interactive confirmation by default and require `--force` in non-interactive mode.
- [Configuration file may contain credentials] → Mitigation: ship `infra-dna.example.toml`, ignore `infra-dna.toml` in git, and ensure error messages do not echo secrets.
- [Parser refactor may affect existing tests and consumer behavior] → Mitigation: keep the external validation contract stable and add tests for separated validation and dispatch paths.
- [Users may expect `infra-dna` to work without config even in load mode] → Mitigation: make `--validate-only` explicitly skip Neo4j config requirements and produce clear config errors only when load mode is requested.

## Migration Plan

1. Add the runtime configuration capability and top-level config schema.
2. Add `infra-dna.example.toml`, ignore `infra-dna.toml` in git, and update documentation to explain copying and configuring the local file.
3. Refactor CLI orchestration so it can validate first and decide on load behavior after validation.
4. Add confirmation and `--force` handling.
5. Integrate Neo4j visitor creation into the CLI using typed configuration from `AppConfigLoader`.
6. Update documentation with config file format, destructive load warning behavior, and CLI examples.

Rollback strategy:
- If the integrated CLI behavior causes issues, users can still fall back to validation-only behavior while the loading integration is corrected.
- The code changes are internal to the CLI and runtime wiring, so rollback is a normal code rollback rather than a data migration.

## Open Questions

- Should the first version require the password to be present in `infra-dna.toml`, or should the design reserve a compatible path for later environment-variable overrides?
- Should `--print-records` print before the confirmation prompt, after loading, or in both validate-only and load modes with the same ordering?
- Should config discovery be strictly current-working-directory based, or should the CLI also support resolving the default config relative to the selected `arch_path`?
