# infra-dna

`infra-dna` is a Python CLI for validating infrastructure graph data stored as YAML under an `arch/` directory.

It performs two passes over the YAML files:

- first pass: reads and validates `entities`
- second pass: reads and validates `relations`

If validation succeeds, it reports how many entities and relations were accepted. If validation fails, it prints all collected errors and exits with a non-zero status.

## Requirements

- Python `3.12+`
- `PyYAML`
- `neo4j`

## Install

The supported local workflow uses a repo-local virtual environment named `.venv`.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Then install the project in editable mode:

```bash
pip install -e .
```

This installs the console script:

```bash
infra-dna
```

The recommended development install is editable so local code changes are reflected without reinstalling.

You can also run the CLI directly through Python from the same activated environment:

```bash
python3 -m infra_dna.cli
```

## Development

Activate the repo-local environment before development work:

```bash
source .venv/bin/activate
```

Run the test suite from the activated environment:

```bash
python3 -m unittest discover -s tests -v
```

If you prefer to invoke the virtual environment directly without activating it:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## CLI Usage

```bash
infra-dna [arch_path] [--print-records]
```

Arguments:

- `arch_path`: optional path to the directory containing YAML files. Defaults to `arch`.
- `--print-records`: print validated entity and relation records after a successful parse.

Examples:

```bash
infra-dna
```

```bash
infra-dna arch
```

```bash
infra-dna ./arch --print-records
```

```bash
python3 -m infra_dna.cli ./arch --print-records
```

Both commands are supported from the configured project environment:

- `infra-dna` is the primary installed CLI
- `python3 -m infra_dna.cli` remains the secondary direct module entrypoint

## Expected YAML Format

The parser discovers all `.yml` and `.yaml` files recursively under the target directory.

Filenames do not define behavior. A file is parsed based on its top-level keys:

- `entities`
- `relations`

A single file may contain either section or both.

### Entities

```yaml
entities:
  - kind: vendor
    key: edgecorp

  - kind: domain
    key: example-app.test
    props:
      monthly_visits: 42000
      monthly_visits_raw: "42K"
```

Rules:

- `entities` must be a list
- each entity must be a mapping
- each entity must have non-empty string fields `kind` and `key`
- `props` is optional, but if present must be a mapping
- entity identity is case-sensitive and unique by `(kind, key)` across all files

### Relations

```yaml
relations:
  - from:
      kind: vendor
      key: edgecorp
    type: provides
    to:
      kind: domain
      key: example-app.test
    props:
      role: cdn
```

Rules:

- `relations` must be a list
- each relation must be a mapping
- each relation must have `from`, `type`, and `to`
- `from` and `to` must be mappings with non-empty string `kind` and `key`
- `type` must start with a lowercase letter and contain only lowercase letters, digits, and underscores
- `props` is optional, but if present must be a mapping
- relation identity is case-sensitive and unique by `(from.kind, from.key, type, to.kind, to.key)` across all files
- relation endpoints must reference entities that exist in the parsed entity set

## Validation Behavior

The parser is strict.

- top-level keys other than `entities` and `relations` are reported as errors
- YAML documents must be mappings
- malformed entity and relation records are reported as errors
- duplicate entities and duplicate relations are reported with all conflicting source locations
- all validation errors are collected and printed together

If the run contains any validation error, no records are dispatched to consumers.

## Neo4j Loading Components

The package also exposes library components for loading validated records into Neo4j:

- `Neo4jService(uri, username, password, database=None)` manages the Neo4j driver, executes queries, clears graph contents, and ensures the `:Entity(kind, key)` uniqueness constraint
- `Neo4jVisitorHandler(service)` implements the parser consumer interface and uses `on_start()` to clear the graph and ensure schema, `on_entity()` to `MERGE` entity nodes, `on_relation()` to `MERGE` relationships, and `on_finish()` to close the service

These components use constructor injection only. They do not read a configuration file, and the current integration point is the Python library rather than a dedicated Neo4j CLI command.

## Successful Output

Example:

```text
Validated 2 entities and 1 relations.
```

With `--print-records`, validated records are printed after a successful parse.

## Error Output

Example:

```text
Unknown top-level keys: relation
  - arch/example.yml:document[0]
Relation references unknown entities: to=(domain, missing-service.test)
  - arch/example.yml:relations[0]
```

## Notes About The Current Repository Data

The current files under [`arch/`](./arch) still use an older schema, so the CLI will report validation errors until those files are migrated to the format documented above.
