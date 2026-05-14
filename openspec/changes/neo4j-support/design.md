## Context

The project already has a strict YAML parser that validates graph data under `arch/` and dispatches only validated records to consumers. The current consumer contract is record-oriented with `on_entity` and `on_relation`, and the parser intentionally validates the full dataset before dispatch so invalid runs never reach downstream consumers.

Neo4j is already a required dependency of the Python project, but there is not yet a supported integration for rebuilding the validated graph into a running Neo4j database. The user wants a constructor-injected service rather than configuration-file-driven setup, and the initial loading workflow should target an existing database by deleting graph contents, recreating required schema, and loading the current YAML snapshot.

This change spans parser lifecycle behavior, a new external system integration, and Cypher generation rules. A design document is useful so the service, consumer, and parser responsibilities stay separated.

## Goals / Non-Goals

**Goals:**
- Introduce a `Neo4jService` that owns connection lifecycle and query execution against a target Neo4j database.
- Introduce a Neo4j-backed consumer/visitor that loads validated entities and relations into Neo4j.
- Extend the consumer contract with lifecycle hooks so stateful consumers can perform setup and teardown around a parse run.
- Rebuild graph contents inside an existing Neo4j database by clearing all nodes and relationships and then ensuring required schema before inserts begin.
- Use `MERGE` for entity and relation loading so repeated successful imports remain idempotent within a rebuilt graph.
- Enforce safe relation type rules needed to interpolate relationship type names into Cypher text.

**Non-Goals:**
- Managing connection details through environment variables or configuration files.
- Dropping and recreating Neo4j databases through administrative DBMS commands.
- Supporting partial streaming into Neo4j before full parser validation completes.
- Adding relationship uniqueness constraints in Neo4j as part of the first version.
- Optimizing for very large bulk imports, batching, or parallel writes in the first version.

## Decisions

### 1. Keep a two-layer integration boundary: service below consumer

The Neo4j integration will be split into:

- `Neo4jService`: low-level database adapter
- `Neo4jVisitorHandler`: graph-aware consumer implementing the parser consumer interface

`Neo4jService` owns driver creation, query execution, graph clearing, schema setup, and connection cleanup. `Neo4jVisitorHandler` owns mapping validated `EntityRecord` and `RelationRecord` objects to Cypher queries and calling the service.

This keeps YAML concerns out of the service and keeps driver/session mechanics out of the consumer logic.

Alternatives considered:
- Let the consumer talk directly to the Neo4j driver: rejected because it mixes graph mapping and connection lifecycle responsibilities.
- Put graph-specific insert helpers directly on the service and skip a visitor layer: rejected because it couples the low-level service to parser record types too early.

### 2. Add lifecycle hooks to the consumer contract

The base consumer contract will be extended with:

- `on_start()`
- `on_finish()`

The parser will call these hooks only during the dispatch phase, after the full parse has completed successfully. This preserves the current invariant that invalid YAML runs do not trigger destructive or partial downstream effects.

`Neo4jVisitorHandler.on_start()` will open or prepare the Neo4j integration workflow. `on_finish()` will close resources.

Alternatives considered:
- Keep only `on_entity` and `on_relation`: rejected because a stateful loader needs explicit setup and teardown.
- Add error hooks now: rejected for the first version because consumers only run after successful validation, so basic lifecycle hooks are enough.

### 3. Rebuild the graph by clearing contents, not by recreating the database

The initial “rebuild from scratch” behavior will mean:

1. connect to the target database
2. clear all current graph contents
3. ensure required schema exists
4. load entities and relations

This avoids DBMS administration commands such as `DROP DATABASE` or `CREATE DATABASE`, avoids edition-specific database-management concerns, and works within the existing target database.

`Neo4jService` will expose explicit methods for this startup sequence, such as:

- `clear_graph()`
- `ensure_schema()`

Alternatives considered:
- Drop and recreate the database: rejected because the clarified requirement is only to rebuild graph contents, not the database itself.
- Leave old graph contents in place and rely only on `MERGE`: rejected because the desired import behavior is a clean rebuild from the current YAML snapshot.

### 4. Use a single `:Entity` node label with composite uniqueness on `(kind, key)`

Nodes will be modeled as:

```text
(:Entity {kind, key, ...props})
```

The required Neo4j schema will include a composite node uniqueness constraint on `:Entity(kind, key)`. `ensure_schema()` will create this constraint idempotently if it does not already exist.

This aligns with the parser’s identity model and keeps the first loader generic across entity kinds.

Alternatives considered:
- Add kind-specific labels such as `:Entity:Vendor` or `:Entity:Domain`: rejected for the first version to keep the graph model and query generation simple.
- Rely only on parser validation without a database constraint: rejected because the database should enforce the core node identity invariant too.

### 5. Use native Neo4j relationship types and `MERGE` for inserts

Entity insertion will use a pattern equivalent to:

```cypher
MERGE (n:Entity {kind: $kind, key: $key})
SET n += $props
```

Relation insertion will use a pattern equivalent to:

```cypher
MATCH (a:Entity {kind: $from_kind, key: $from_key})
MATCH (b:Entity {kind: $to_kind, key: $to_key})
MERGE (a)-[r:provides]->(b)
SET r += $props
```

Using native relationship types keeps the stored graph natural to query and aligns with the logical relation identity already defined by the parser.

Alternatives considered:
- Store every edge under a generic relationship type with a `type` property: rejected because it weakens the graph model and makes Cypher queries less natural.
- Use `CREATE` for relations and rely only on a clean database: rejected because `MERGE` provides safer idempotent behavior within a run and across repeated clean imports.

### 6. Constrain relation type names so they are safe to interpolate into Cypher

Relationship type names cannot be treated like normal value parameters in the same way properties can. The relation type becomes part of the Cypher query text, so the parser will enforce a strict lowercase naming rule for relation types.

The expected rule is:

- lowercase only
- must start with a letter
- remaining characters limited to lowercase letters, digits, and underscores

Representative pattern:

```text
^[a-z][a-z0-9_]*$
```

This keeps Cypher generation simple and avoids unsafe or ambiguous query construction.

Alternatives considered:
- Continue allowing unconstrained relation type strings: rejected because the loader needs to embed relationship type names into Cypher text.
- Normalize author input to uppercase or another style at load time: rejected because the desired authoring convention is lowercase end-to-end.

## Risks / Trade-offs

- Destructive startup behavior clears the full graph before loading. → Mitigation: run Neo4j loading only after the parser has fully validated the dataset, and keep the destructive logic confined to `on_start()`.
- Constraint creation may fail if pre-existing data violates the intended schema. → Mitigation: clear the graph before ensuring schema in the rebuild flow.
- Dynamic Cypher for relationship types can become unsafe if validation is weak. → Mitigation: enforce a strict lowercase relation-type pattern in the parser before any Neo4j dispatch occurs.
- A simple per-record write strategy may be slower on larger datasets. → Mitigation: keep the first version simple and leave batching as a later optimization if needed.
- Adding lifecycle hooks changes the consumer contract. → Mitigation: provide no-op defaults in the base consumer so existing consumers remain easy to update.

## Migration Plan

1. Extend the consumer interface with `on_start()` and `on_finish()` default no-op methods.
2. Update parser dispatch so lifecycle hooks wrap entity and relation dispatch, but only on successful parse results.
3. Add stricter relation type validation to the parser.
4. Add the Neo4j service module with connection, read/write execution, graph clearing, schema setup, and cleanup behavior.
5. Add the Neo4j visitor/consumer that maps validated records into Cypher using the service.
6. Add tests for lifecycle dispatch, relation type validation, service behavior, and Neo4j-oriented consumer behavior.
7. Update CLI or usage documentation as needed to describe how the Neo4j loading path is invoked once implemented.

Rollback is straightforward because this change is additive at the code level: the Neo4j integration can be removed or disabled without changing the validated YAML schema itself, aside from the stricter relation type rule.

## Open Questions

- Should the first version expose the Neo4j loading path through the existing CLI immediately, or should the initial implementation keep it as a library capability first?
- Should `Neo4jService` use explicit `connect()` semantics, lazy connection creation, or context-manager support in the first version?
- Should the service return raw Neo4j driver results for reads, or normalize them into plain Python structures from the start?
