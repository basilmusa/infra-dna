## ADDED Requirements

### Requirement: Neo4j service connects through constructor-injected parameters
The system SHALL provide a `Neo4jService` that connects to a target Neo4j database using connection parameters supplied through its constructor. The service MUST NOT require a configuration file to establish the connection. The service SHALL support executing Cypher queries against the configured database and closing the underlying Neo4j connection when loading is complete.

#### Scenario: Service is created with explicit connection parameters
- **WHEN** application code instantiates `Neo4jService` with a URI, credentials, and an optional database name
- **THEN** the service is able to use those injected constructor parameters to operate against the target Neo4j database without reading a configuration file

#### Scenario: Service executes a query against the configured database
- **WHEN** application code invokes the Neo4j service query execution API with Cypher text and parameters
- **THEN** the service executes that query against the configured target database

#### Scenario: Service closes database resources
- **WHEN** application code signals that Neo4j loading is finished
- **THEN** the service closes the underlying Neo4j connection resources

### Requirement: Neo4j loading rebuilds graph contents inside the target database
The system SHALL load validated YAML graph data into an existing Neo4j database by clearing the current graph contents and then recreating required schema before any entity or relation records are inserted. The first version MUST rebuild graph contents within the existing target database and MUST NOT require dropping and recreating the database itself.

#### Scenario: Loading startup clears existing graph contents
- **WHEN** a Neo4j-backed loading run begins
- **THEN** the loading workflow clears all existing nodes and relationships from the target database before inserting new records

#### Scenario: Loading startup avoids database recreation
- **WHEN** a Neo4j-backed loading run begins
- **THEN** the loading workflow rebuilds graph contents inside the existing database rather than issuing administrative database recreation commands

### Requirement: Neo4j loading ensures node identity schema before inserts
The system SHALL ensure the required Neo4j node identity schema exists before entity and relation insertion begins. For the first version, the required schema MUST include a composite uniqueness constraint on `:Entity(kind, key)`. Schema setup MUST be safe to run repeatedly across multiple loading runs.

#### Scenario: Loader ensures the entity uniqueness constraint
- **WHEN** Neo4j loading startup runs schema setup
- **THEN** the loader ensures a composite uniqueness constraint exists for `:Entity(kind, key)`

#### Scenario: Schema setup is idempotent
- **WHEN** Neo4j loading startup runs schema setup more than once
- **THEN** repeated schema setup does not require duplicate manual cleanup before the next run

### Requirement: Neo4j loader stores entities as generic Entity nodes
The system SHALL load entity records into Neo4j as nodes with the `:Entity` label and identity properties `kind` and `key`. The loader SHALL use `MERGE` on `(kind, key)` so the persisted node identity matches the parser identity model.

#### Scenario: Loader merges an entity node by kind and key
- **WHEN** the Neo4j visitor receives a validated entity record
- **THEN** it loads that entity into Neo4j by merging a `:Entity` node keyed by the record’s `kind` and `key`

#### Scenario: Loader applies entity properties after merge
- **WHEN** the Neo4j visitor loads a validated entity record that includes `props`
- **THEN** it applies those properties onto the merged `:Entity` node

### Requirement: Neo4j loader stores relations with native relationship types
The system SHALL load validated relations between `:Entity` nodes using native Neo4j relationship types derived from the validated relation `type` field. The loader SHALL resolve relation endpoints by matching `:Entity` nodes on `(kind, key)` and SHALL use `MERGE` when creating the relationship.

#### Scenario: Loader merges a relationship between existing entity nodes
- **WHEN** the Neo4j visitor receives a validated relation record
- **THEN** it matches the `from` and `to` entity nodes by `kind` and `key` and merges a relationship of the validated type between them

#### Scenario: Loader applies relation properties after merge
- **WHEN** the Neo4j visitor loads a validated relation record that includes `props`
- **THEN** it applies those properties onto the merged relationship

### Requirement: Neo4j loading uses parser lifecycle hooks for setup and teardown
The system SHALL integrate Neo4j loading through the parser consumer lifecycle so Neo4j setup occurs before any record dispatch and cleanup occurs after dispatch completes. The Neo4j visitor SHALL perform graph clearing and schema setup during `on_start()` and SHALL close the Neo4j service during `on_finish()`.

#### Scenario: Neo4j visitor prepares the database on start
- **WHEN** the parser begins dispatching a valid parse result to a Neo4j-backed consumer
- **THEN** the Neo4j visitor performs graph clearing and schema setup before any entity or relation records are written

#### Scenario: Neo4j visitor closes the service on finish
- **WHEN** the parser completes dispatching a valid parse result to a Neo4j-backed consumer
- **THEN** the Neo4j visitor closes the Neo4j service during the finish lifecycle hook
