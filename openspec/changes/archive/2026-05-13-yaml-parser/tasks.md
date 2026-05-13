## 1. Parser Foundation

- [x] 1.1 Create the Python module structure for the YAML parser and define canonical entity and relation record models with source-location metadata.
- [x] 1.2 Implement recursive YAML file discovery under `arch/` and shared document loading utilities.
- [x] 1.3 Implement strict top-level document validation so only `entities` and `relations` are accepted as recognized keys.

## 2. Entity Pass

- [x] 2.1 Implement the first parsing pass that scans all discovered YAML files and emits records from `entities` sections only.
- [x] 2.2 Validate entity record structure, including required `kind` and `key` fields and optional `props` mapping.
- [x] 2.3 Track global case-sensitive entity identities and accumulate duplicate entity errors with all conflicting source locations.

## 3. Relation Pass

- [x] 3.1 Implement the second parsing pass that scans all discovered YAML files and emits records from `relations` sections only.
- [x] 3.2 Validate relation record structure, including `from`, `type`, `to`, endpoint identity fields, and optional `props` mapping.
- [x] 3.3 Track global case-sensitive relation identities and accumulate duplicate relation errors with all conflicting source locations.
- [x] 3.4 Enforce strict relation endpoint validation against entities discovered in the entity pass.

## 4. Error Reporting And Consumer Dispatch

- [x] 4.1 Implement aggregated validation error collection and final non-zero failure behavior when any error is present.
- [x] 4.2 Define the consumer callback or class interface for receiving validated entity and relation records.
- [x] 4.3 Implement a `PrintToConsole` consumer that prints parsed entities and relations for inspection.
- [x] 4.4 Ensure consumer dispatch occurs only for records that have passed parser validation for their phase.

## 5. Verification

- [x] 5.1 Add test fixtures covering recursive discovery, mixed files with both `entities` and `relations`, and filename-independent parsing.
- [x] 5.2 Add tests for strict top-level validation, malformed records, missing required fields, and invalid `props` values.
- [x] 5.3 Add tests for duplicate entity and relation reporting that verify all conflicting occurrences are included.
- [x] 5.4 Add tests for strict missing-entity relation references and successful dispatch to a sample consumer.
