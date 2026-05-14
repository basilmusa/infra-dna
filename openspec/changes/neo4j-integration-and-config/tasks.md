## 1. Runtime Configuration

- [x] 1.1 Add typed runtime configuration models for `AppConfig` and `Neo4jConfig`
- [x] 1.2 Add an `AppConfigLoader` that reads `infra-dna.toml`, validates required Neo4j settings, and supports a `--config` override path
- [x] 1.3 Add `infra-dna.example.toml` documenting the expected Neo4j config keys
- [x] 1.4 Update `.gitignore` to exclude the local `infra-dna.toml` file while keeping the example file tracked

## 2. Parser And CLI Flow

- [x] 2.1 Refactor parser orchestration so validation can complete and return a parse result before consumer dispatch is triggered
- [x] 2.2 Update the parser dispatch path so valid parse results can be dispatched explicitly to configured consumers after a higher-level caller decides to proceed
- [x] 2.3 Update `infra_dna/cli.py` to support `--validate-only`, `--config`, and `--force`
- [x] 2.4 Implement CLI confirmation behavior so interactive destructive loads prompt after successful validation and non-interactive destructive loads require `--force`
- [x] 2.5 Ensure `--validate-only` skips Neo4j config requirements and never triggers Neo4j loading

## 3. Neo4j CLI Integration

- [x] 3.1 Wire `AppConfigLoader` into the CLI and construct `Neo4jService` and `Neo4jVisitorHandler` only after config loading succeeds
- [x] 3.2 Integrate Neo4j loading into the CLI so successful non-validate-only runs dispatch validated records to the Neo4j visitor
- [x] 3.3 Preserve the existing clear-graph, ensure-schema, and `MERGE`-based load behavior under the new CLI-controlled workflow
- [x] 3.4 Update success and failure messaging so users can distinguish validation-only results, cancelled loads, config failures, and successful Neo4j reloads

## 4. Verification And Documentation

- [x] 4.1 Add tests for configuration file loading, missing required Neo4j settings, typed config construction, and config override behavior
- [x] 4.2 Add tests for parser or CLI separation between validation and dispatch, including the guarantee that invalid results never trigger Neo4j loading
- [x] 4.3 Add CLI tests for `--validate-only`, `--force`, interactive confirmation flow, and non-interactive refusal without `--force`
- [x] 4.4 Update `README.md` with the example-config copy flow, config file format, destructive-load warning behavior, and end-to-end CLI usage
