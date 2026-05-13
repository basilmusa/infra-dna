## Why

The repository stores infrastructure entities and relations as YAML in `arch/`, but there is no parser that validates those documents and turns them into a dependable processing pipeline. The project needs a Python parser that walks the YAML files incrementally, enforces uniqueness and structural rules, and exposes parsed entities and relations to pluggable handlers before any Neo4j loading is attempted.

## What Changes

- Add a Python program that reads `entity-*.yml` files first, then `relation-*.yml` files, processing each file and record incrementally rather than requiring all data to be loaded into memory at once.
- Define internal entity and relation representations that are yielded or passed to handler callbacks one record at a time.
- Design the parser to accept pluggable handler classes or callback implementations so different behaviors can be attached to the same parsing flow.
- Support handlers such as a validation-oriented handler that checks case-sensitive uniqueness constraints and a console-printing handler for simple inspection.
- Establish validation behavior that reports duplicate entity `(kind, key)` tuples, duplicate relations, and other invalid inputs, then exits with failure instead of continuing with partial results.
- Keep Neo4j insertion out of immediate scope, but shape the parser/handler interface so a future `Neo4jLoader` can consume the parsed stream directly.

## Capabilities

### New Capabilities
- `yaml-graph-parser`: Parse infrastructure YAML documents incrementally and dispatch validated entity and relation records to pluggable handlers.

### Modified Capabilities

## Impact

- Affected code: new Python parser, record models, and handler interface for processing files under `arch/`
- Affected data: `entity-*.yml` and `relation-*.yml` become validated streaming inputs with enforced uniqueness constraints
- Affected systems: future validators, console processors, and Neo4j loaders will plug into the parser pipeline
- Dependencies: Python YAML parsing support and consistent validation/error-reporting behavior
