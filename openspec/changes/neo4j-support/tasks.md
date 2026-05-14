## 1. Parser Contract Updates

- [x] 1.1 Extend `GraphConsumer` with no-op `on_start()` and `on_finish()` lifecycle hooks and update existing consumer implementations to remain compatible
- [x] 1.2 Update parser dispatch so `on_start()` runs before any entity or relation dispatch and `on_finish()` runs after all dispatch, only when the parse result is valid
- [x] 1.3 Tighten relation `type` validation to require the lowercase safe pattern and add aggregated validation errors for invalid relation type values

## 2. Neo4j Service Layer

- [x] 2.1 Add a `Neo4jService` module that accepts constructor-injected connection parameters and manages the Neo4j driver lifecycle
- [x] 2.2 Implement Neo4j query execution methods for write and read operations against the configured database
- [x] 2.3 Implement `clear_graph()` to remove all nodes and relationships from the configured database
- [x] 2.4 Implement `ensure_schema()` so it idempotently creates the `:Entity(kind, key)` composite uniqueness constraint
- [x] 2.5 Add tests for Neo4j service connection setup, query execution behavior, graph clearing, schema setup, and cleanup behavior using mocks or fakes

## 3. Neo4j Consumer Integration

- [x] 3.1 Add a `Neo4jVisitorHandler` that implements the consumer interface and uses `Neo4jService` for all database operations
- [x] 3.2 Implement `Neo4jVisitorHandler.on_start()` to prepare the target database by clearing graph contents and ensuring schema before any records are written
- [x] 3.3 Implement entity loading with `MERGE (n:Entity {kind, key})` and property application from validated entity records
- [x] 3.4 Implement relation loading by matching endpoint `:Entity` nodes, merging native relationship types from validated relation records, and applying relation properties
- [x] 3.5 Implement `Neo4jVisitorHandler.on_finish()` to close the Neo4j service after dispatch completes

## 4. Verification And Documentation

- [x] 4.1 Add parser tests covering lifecycle hook ordering and the guarantee that invalid parse results do not invoke any consumer lifecycle or record callbacks
- [x] 4.2 Add parser tests covering valid and invalid relation type values for the lowercase safe pattern
- [x] 4.3 Add integration-oriented tests for the Neo4j visitor using mocked service calls to verify startup, entity loading, relation loading, and teardown order
- [x] 4.4 Update project documentation to describe the Neo4j loading components, constructor-injected connection parameters, and the graph rebuild behavior inside the target database
