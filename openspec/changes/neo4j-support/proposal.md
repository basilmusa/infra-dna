## Why

The project can already validate infrastructure graph YAML, but it does not yet provide a supported way to load validated entities and relations into a running Neo4j database. Adding a Neo4j service and visitor-based loader is the next step so the validated graph data can be rebuilt into Neo4j in a repeatable way.

## What Changes

- Add a Neo4j integration capability centered on a constructor-injected `Neo4jService` that can connect to a target database, execute queries, clear the current graph contents, and ensure required schema exists.
- Add a Neo4j visitor/consumer that uses the existing parser output to load entities and relations into Neo4j after validation succeeds.
- Extend the consumer lifecycle with `on_start` and `on_finish` hooks so stateful consumers can perform setup and teardown around a parse run.
- Define the initial Neo4j loading behavior to rebuild the graph contents inside an existing database, recreate required schema, and load entities and relations with `MERGE`.
- Tighten relation type requirements so relationship names are lowercase and safe to interpolate into Cypher query text.

## Capabilities

### New Capabilities
- `neo4j-graph-loading`: Connect to a running Neo4j database and load validated entities and relations through a service-backed consumer workflow.

### Modified Capabilities
- `yaml-graph-parser`: Extend the consumer contract with lifecycle hooks and enforce stricter relation type requirements needed for safe Neo4j relationship loading.

## Impact

- Affected code: `infra_dna/parser.py`, `infra_dna/consumers.py`, CLI-facing integration points, and new Neo4j service/handler modules
- Affected systems: local Neo4j database reached over Bolt
- Dependencies: existing required `neo4j` Python driver will be used by a first-class service layer
- Tests and docs: new coverage for lifecycle behavior, Neo4j service behavior, and graph loading expectations
