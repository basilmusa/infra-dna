## Why

The project can already validate YAML and can already load validated records into Neo4j through library components, but the primary `infra-dna` CLI does not yet connect those pieces into one end-to-end workflow. This change is needed so a normal CLI run can validate the graph, confirm the destructive reload behavior, and then rebuild the configured Neo4j database using a supported runtime configuration file.

## What Changes

- Add a dedicated configuration service that reads a top-level runtime configuration file for Neo4j connection settings and returns typed application configuration to the CLI.
- Integrate Neo4j loading into the `infra-dna` CLI so that successful runs validate YAML first and then load Neo4j through `Neo4jVisitorHandler`.
- Add CLI flags for `--validate-only`, config file override, and confirmation bypass for non-interactive or automation use.
- Introduce a confirmation flow for destructive graph reloads so interactive users are warned before all nodes and relationships in the configured Neo4j database are cleared and rebuilt.
- Refine parser and dispatch flow as needed so validation can complete before the CLI decides whether to proceed with destructive Neo4j loading.

## Capabilities

### New Capabilities
- `runtime-configuration`: Load and validate top-level application configuration for Neo4j connection settings through a dedicated configuration service.

### Modified Capabilities
- `neo4j-graph-loading`: Change Neo4j loading from library-only usage to CLI-driven loading that runs automatically after successful validation, using runtime configuration and interactive confirmation safeguards.
- `yaml-graph-parser`: Change CLI behavior so `infra-dna` can validate first, optionally skip loading with `--validate-only`, and only proceed to destructive Neo4j dispatch after explicit confirmation or confirmation bypass.

## Impact

- Affected code: `infra_dna/cli.py`, new configuration module(s), parser orchestration or dispatch flow, Neo4j loading integration, and related tests.
- Affected interfaces: the primary `infra-dna` CLI contract and its runtime behavior.
- Affected systems: local Neo4j databases targeted by the configured load workflow, plus project documentation for setup and operation.
