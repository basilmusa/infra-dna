## MODIFIED Requirements

### Requirement: Parser validates relation structure, references, and uniqueness
The system SHALL require each relation record to be a mapping with `from`, `type`, and `to` fields. The `from` and `to` fields MUST each contain non-empty string `kind` and `key` fields. The `type` field MUST be a non-empty lowercase string that starts with a letter and contains only lowercase letters, digits, and underscores. If present, `props` MUST be a mapping. Relation identity MUST be case-sensitive and MUST be globally unique across all scanned YAML files using the tuple `(from.kind, from.key, type, to.kind, to.key)`. Relation endpoints MUST reference existing entities discovered during the entity pass.

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

#### Scenario: Relation type must use the lowercase safe pattern
- **WHEN** a relation record provides a `type` value that is empty, contains uppercase letters, starts with a non-letter, or contains characters other than lowercase letters, digits, or underscores
- **THEN** the parser reports a validation error for that relation record

### Requirement: Parser dispatches validated records to pluggable consumers
The system SHALL expose entities and relations as canonical parsed records to pluggable consumer callbacks or classes. The parser MUST support consumers such as console printing and Neo4j loading without requiring those consumers to re-parse YAML documents. The consumer contract SHALL include lifecycle hooks for `on_start()` and `on_finish()`. The parser MUST invoke consumer lifecycle hooks only after the full parse result is valid, and it MUST invoke `on_start()` before dispatching any entity or relation records and `on_finish()` after dispatching all entity and relation records.

#### Scenario: Consumer lifecycle starts before record dispatch
- **WHEN** the parser has completed a valid parse result and begins dispatching to configured consumers
- **THEN** it invokes each consumer’s `on_start()` before dispatching any entity records or relation records

#### Scenario: Consumer receives parsed entities
- **WHEN** the parser dispatches a successfully validated entity record
- **THEN** it dispatches that entity to the configured consumer interface

#### Scenario: Consumer receives parsed relations
- **WHEN** the parser dispatches a successfully validated relation record
- **THEN** it dispatches that relation to the configured consumer interface

#### Scenario: Consumer lifecycle finishes after record dispatch
- **WHEN** the parser completes dispatching all validated entity and relation records to configured consumers
- **THEN** it invokes each consumer’s `on_finish()`

#### Scenario: Invalid parse result does not trigger consumer lifecycle
- **WHEN** the parser has collected one or more validation errors
- **THEN** it does not invoke `on_start()`, `on_entity()`, `on_relation()`, or `on_finish()` for configured consumers
