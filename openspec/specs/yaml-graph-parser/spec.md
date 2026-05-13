## Purpose

Define the expected behavior for discovering, validating, and dispatching YAML graph records parsed from `arch/`.

## Requirements

### Requirement: Parser discovers YAML documents by strict top-level schema
The system SHALL recursively scan YAML files under `arch/` and determine whether a file contributes entity records, relation records, or both based on the presence of top-level `entities` and `relations` keys. The parser MUST NOT assign semantics based on filename patterns. Top-level keys other than `entities` and `relations` MUST be treated as validation errors.

#### Scenario: File contributes entities by top-level key
- **WHEN** a YAML file under `arch/` contains an `entities` top-level key
- **THEN** the parser treats that file as a source of entity records regardless of its filename

#### Scenario: File contributes relations by top-level key
- **WHEN** a YAML file under `arch/` contains a `relations` top-level key
- **THEN** the parser treats that file as a source of relation records regardless of its filename

#### Scenario: Unknown top-level key is rejected
- **WHEN** a YAML file contains a top-level key other than `entities` or `relations`
- **THEN** the parser reports a validation error for the unknown top-level key

### Requirement: Parser processes entities before relations
The system SHALL make two ordered passes over the discovered YAML files. In the first pass it MUST parse and validate entity records. In the second pass it MUST parse and validate relation records. A file MAY contain both `entities` and `relations`, and the parser MUST process its entities during the first pass and its relations during the second pass.

#### Scenario: Mixed document participates in both passes
- **WHEN** a YAML file contains both `entities` and `relations`
- **THEN** the parser processes the `entities` section during the entity pass and the `relations` section during the relation pass

#### Scenario: Relation validation waits until entities are known
- **WHEN** the parser begins relation processing
- **THEN** all entity identities discovered in the entity pass are available for relation endpoint validation

### Requirement: Parser validates entity structure and uniqueness
The system SHALL require each entity record to be a mapping with non-empty string `kind` and `key` fields. If present, `props` MUST be a mapping. Entity identity MUST be case-sensitive and MUST be globally unique across all scanned YAML files using the tuple `(kind, key)`.

#### Scenario: Duplicate entity identity is reported
- **WHEN** two or more entity records define the same case-sensitive `(kind, key)` tuple
- **THEN** the parser reports a duplicate entity validation error for that identity

#### Scenario: Entity props must be a mapping
- **WHEN** an entity record includes `props` with a non-mapping value
- **THEN** the parser reports a validation error for that entity record

#### Scenario: Entity missing required identity fields is rejected
- **WHEN** an entity record omits `kind` or `key`, or provides either as an empty or non-string value
- **THEN** the parser reports a validation error for that entity record

### Requirement: Parser validates relation structure, references, and uniqueness
The system SHALL require each relation record to be a mapping with `from`, `type`, and `to` fields. The `from` and `to` fields MUST each contain non-empty string `kind` and `key` fields. If present, `props` MUST be a mapping. Relation identity MUST be case-sensitive and MUST be globally unique across all scanned YAML files using the tuple `(from.kind, from.key, type, to.kind, to.key)`. Relation endpoints MUST reference existing entities discovered during the entity pass.

#### Scenario: Duplicate relation identity is reported
- **WHEN** two or more relation records define the same case-sensitive `(from.kind, from.key, type, to.kind, to.key)` tuple
- **THEN** the parser reports a duplicate relation validation error for that identity

#### Scenario: Relation reference to unknown entity is reported
- **WHEN** a relation endpoint references an entity identity that was not discovered during the entity pass
- **THEN** the parser reports a validation error for the missing entity reference

#### Scenario: Relation props must be a mapping
- **WHEN** a relation record includes `props` with a non-mapping value
- **THEN** the parser reports a validation error for that relation record

#### Scenario: Relation missing required fields is rejected
- **WHEN** a relation record omits `from`, `type`, or `to`, or provides invalid endpoint identity fields
- **THEN** the parser reports a validation error for that relation record

### Requirement: Parser aggregates validation errors before failing
The system SHALL collect all validation errors discovered across all scanned YAML files and report them together at the end of the run. If any validation error is collected, the parser MUST exit with failure status. Each reported error MUST include source context sufficient to identify the offending record, including file path and record location or identity. For duplicate records, the report MUST include all conflicting occurrences for the duplicated identity.

#### Scenario: Multiple invalid records are reported together
- **WHEN** the scanned YAML input contains more than one validation error
- **THEN** the parser completes validation across the full input set and reports all collected errors in one result

#### Scenario: Duplicate report includes all conflicting occurrences
- **WHEN** a duplicate entity or relation identity is found more than once
- **THEN** the reported error includes the source location of every conflicting occurrence for that identity

### Requirement: Parser dispatches validated records to pluggable consumers
The system SHALL expose entities and relations as canonical parsed records to pluggable consumer callbacks or classes. The parser MUST support consumers such as console printing and future Neo4j loading without requiring those consumers to re-parse YAML documents.

#### Scenario: Consumer receives parsed entities
- **WHEN** the parser successfully validates an entity record during the entity pass
- **THEN** it dispatches that entity to the configured consumer interface

#### Scenario: Consumer receives parsed relations
- **WHEN** the parser successfully validates a relation record during the relation pass
- **THEN** it dispatches that relation to the configured consumer interface

### Requirement: Parser CLI is exposed as infra-dna
The system SHALL expose the installed parser CLI through the `infra-dna` command name as the primary user-facing executable for project workflows.

#### Scenario: Installed CLI uses the new command name
- **WHEN** the project is installed through the supported package workflow
- **THEN** the primary installed console command is `infra-dna`

### Requirement: Parser remains executable as a Python module
The system SHALL continue to support direct module execution through `python -m infra_dna.cli` in addition to the installed `infra-dna` console command.

#### Scenario: Module execution remains supported
- **WHEN** a user runs `python -m infra_dna.cli` from a correctly configured project environment
- **THEN** the parser CLI executes successfully without requiring the installed console script name
