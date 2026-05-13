## Context

The repository stores infrastructure graph data as YAML under `arch/`. This change introduces a Python parser that validates and parses those documents incrementally, then dispatches entities and relations to pluggable consumers such as a console printer or a future Neo4j loader.

Several requirements now define the architecture:

- The parser must recurse through subdirectories under `arch/`.
- Filenames are not semantic. What matters is whether a YAML document contains `entities:` and/or `relations:`.
- The parser must scan all YAML files twice: once to process entities, then again to process relations.
- Validation should collect all discovered errors and report them together.
- Relation endpoint validation is strict: relations may only reference entities that exist in the scanned input set.
- Unknown top-level keys should be ignored for now.

Given those constraints, moving validation into the parser simplifies the design. The parser can own structural checks, uniqueness tracking, and strict entity-reference validation while still exposing parsed records incrementally to pluggable consumers.

## Goals / Non-Goals

**Goals:**

- Provide a stream-oriented Python parser that recursively scans all YAML files under `arch/`.
- Perform two ordered passes over the same file set: first `entities`, then `relations`.
- Define canonical internal representations for entities and relations with explicit identity fields and optional properties.
- Build validation into the parser so it enforces structural rules, global uniqueness, and strict relation endpoint references.
- Accumulate all validation errors across the run and exit non-zero if any are found.
- Allow pluggable consumer callbacks or classes such as `PrintToConsole` and a future `Neo4jLoader`.

**Non-Goals:**

- Writing to Neo4j in this change.
- Treating filenames such as `entity-*.yml` or `relation-*.yml` as parser inputs.
- Supporting legacy `groups` structures.
- Building a full graph object that must hold every parsed record before any consumer sees them.

## Decisions

### 1. Discover all YAML files recursively and ignore filename semantics

The parser will recursively discover YAML files under `arch/`. It will not infer behavior from filenames. A file participates in entity parsing if it contains an `entities` top-level key and in relation parsing if it contains a `relations` top-level key.

This keeps the schema content-driven and allows future files to contain both sections without special treatment.

Alternative considered:

- Use `entity-*.yml` and `relation-*.yml` as the authoritative discovery convention.
  This was rejected because it makes filenames part of the data contract and limits future organization.

### 2. Use two content-based passes over the same file set

The parser will process the discovered files twice:

1. First pass: read and validate entity records under `entities`.
2. Second pass: read and validate relation records under `relations`.

This ensures all entity identities are known before relation validation begins. A file that contains both sections will naturally contribute to both passes.

Alternative considered:

- Single-pass parsing with in-order handling of both sections.
  This was rejected because strict relation endpoint validation would then depend on file ordering or require buffering unresolved relations.

### 3. Move validation into the parser

Validation should be part of the parser rather than a separate `Validator` handler. This simplifies the pipeline because the parser already controls discovery order, document decoding, and record normalization.

The parser will own:

- top-level document validation
- record shape validation
- rejection of `groups`
- global entity uniqueness tracking
- global relation uniqueness tracking
- strict relation endpoint validation
- accumulation and reporting of all errors

Consumers such as `PrintToConsole` and `Neo4jLoader` will only receive records if parsing reaches the relevant phase. They are not responsible for correctness policy.

Alternative considered:

- Use a separate `Validator` consumer class.
  This was rejected because the parser would still need to coordinate pass ordering and schema interpretation, so separating validation adds complexity without enough benefit at this stage.

### 4. Use canonical record models with exact identity semantics

Parsed entities should be normalized into records with fields equivalent to:

- `kind`
- `key`
- `props`
- source metadata such as file path and record index

Parsed relations should be normalized into records with fields equivalent to:

- `from_kind`
- `from_key`
- `type`
- `to_kind`
- `to_key`
- `props`
- source metadata

Identity is case-sensitive.

Entity uniqueness is defined by:

`(kind, key)`

Relation uniqueness is defined by:

`(from_kind, from_key, type, to_kind, to_key)`

Properties do not participate in uniqueness. Duplicate relation endpoints and type are invalid even if properties differ.

Alternative considered:

- Pass raw dictionaries directly to consumers.
  This was rejected because canonical records create a cleaner contract and enable precise error reporting.

### 5. Validate structure immediately and semantics across the full run

The parser should perform structural checks as soon as each document is read:

- top-level `entities`, if present, must be a list
- top-level `relations`, if present, must be a list
- unknown top-level keys are ignored
- each entity or relation item must be a mapping
- required fields must exist and be non-empty strings
- `props`, if present, must be a mapping
- entity documents must not use `groups`

The parser should also maintain run-wide state for semantic validation:

- seen entity identities with their original source locations
- seen relation identities with their original source locations
- the set of known entities available for strict relation endpoint checks

This split keeps malformed records local while still allowing cross-file validation.

### 6. Accumulate all errors and fail at the end

The parser should never stop at the first duplicate or invalid reference. Instead, it should collect all errors discovered while scanning files and then emit a complete report before exiting non-zero.

Each error should include:

- file path
- record position or identity
- description of the rule violation
- original conflicting source location when relevant

This makes a single run actionable, especially when many duplicates or bad references exist.

Alternative considered:

- Fail fast on the first error.
  This was rejected because the requirement is to surface all invalid conditions in one pass of the tool.

### 7. Keep consumers pluggable and observational

The parser should accept a consumer callback or class-based consumer interface for behaviors such as:

- printing entities and relations to the console
- collecting records for tests
- loading records into Neo4j in a future change

Because validation is built-in, consumers can assume any delivered record has already passed parser-level validation for its phase.

Alternative considered:

- Make consumers responsible for partial validation.
  This was rejected because correctness rules should remain centralized.

## Risks / Trade-offs

- [Parsing all files twice increases file I/O] → The YAML corpus is expected to be small, and the simplicity of strict two-phase processing is worth the cost.
- [Built-in validation couples policy to the parser] → Keep validation rules scoped to the YAML contract and expose only canonical validated records to consumers.
- [A file containing both entities and relations is parsed twice] → This is intentional and preserves strict phase ordering without complex buffering.
- [Aggregated validation requires in-memory tracking of seen identities] → Track only identities and source metadata, not full graph state.
- [Unknown top-level keys may hide author mistakes] → Ignore them for now as requested, while preserving the option to warn in a later change.

## Migration Plan

There is no runtime migration requirement because this change introduces a new parser pipeline rather than modifying an existing loader. Adoption can proceed in stages:

1. Normalize YAML documents under `arch/` to use `entities` and `relations` top-level sections with no `groups`.
2. Implement the recursive two-pass parser with built-in validation and canonical record normalization.
3. Implement a simple `PrintToConsole` consumer to verify traversal and record dispatch.
4. Add a future `Neo4jLoader` consumer once the parser contract is stable.

## Open Questions

- Should the parser continue delivering valid records to consumers if some errors have already been collected earlier in the run, or should consumer dispatch be suppressed once any validation error is seen?
- Should duplicate reporting include only the first conflicting source location or all conflicting occurrences for the same identity?
- Should the parser expose a single unified consumer interface, or separate entity and relation callback hooks for simpler implementations?
