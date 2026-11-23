# VetPath MCP

**Structured, source-aware military-to-VA transition information through the Model Context Protocol**

VetPath MCP is a read-only Model Context Protocol server developed for the 2026 GSA Model Context Protocol and SI Agent Government Hackathon.

The prototype provides AI clients with discoverable tools for retrieving and interpreting military-to-VA transition information through structured response contracts and source-provenance metadata.

## Use Case

Military-to-civilian transition information is distributed across multiple programs, resources, timelines, and specialized terms.

VetPath provides a consistent MCP interface for:

- Finding reviewed Veteran transition resources.
- Retrieving structured program information.
- Identifying phase-based transition milestones.
- Resolving military and VA terminology.
- Returning source-aware, machine-readable responses.

## MCP Tools

VetPath exposes four read-only MCP tools.

### `search_veteran_resources`

Searches a curated catalog of official Veteran transition resources.

### `get_program_details`

Retrieves structured information about a specific program or resource by catalog identifier.

### `get_transition_milestones`

Returns reviewed transition milestones for a selected transition phase, with optional service-category filtering.

### `resolve_military_terminology`

Resolves military and VA terminology and acronyms with contextual definitions and source provenance.

## Architecture

The locally validated execution path is:

```text
MCP Client
    |
    v
Local stdio transport
    |
    v
FastMCP VetPath Server
    |
    v
Typed, source-aware response
```

The implementation uses:

- Python
- FastMCP
- MCP Python SDK
- Pydantic response models
- Curated JSON resource and terminology catalogs
- Explicit tool registration
- Source-provenance metadata
- Pytest
- Ruff
- `uv` dependency management

## Project Structure

```text
main.py
pyproject.toml
uv.lock
src/
  vetpath_mcp/
    app.py
    config.py
    models.py
    routes.py
    vetpath_models.py
    data/
    prompts/
    resources/
    tools/
tests/
docs/
eval/
deploy/
```

## Local Setup

### Prerequisites

Install Python 3.11 and `uv`.

```bash
pip install uv
```

### Install dependencies

```bash
uv sync --group dev
```

### Run the server

```bash
uv run python main.py
```

The default local transport is `stdio`. The server waits for an MCP client to connect through standard input and output and does not display a browser URL.

## Validation

The original VetPath server was validated in Databricks using the project's automated test suite and a genuine MCP client.

Observed results:

```text
Automated tests:       65 passed, 0 failed
Ruff code check:       All checks passed
MCP initialization:    Passed
Protocol version:      2025-11-25
Tools discovered:      4
DD214 tool invocation: Passed
```

The end-to-end MCP example invoked:

```text
resolve_military_terminology({"term": "DD214"})
```

The structured response included:

```text
concept_id:             records.dd214
preferred_label:        DD Form 214
requires_clarification: false
errors:                 []
is_error:               false
result_type:            complete
```

The response also included source-provenance metadata referencing an official federal source.

## Testing

Run the automated test suite:

```bash
PYTHONPYCACHEPREFIX=/tmp/vetpath-pycache \
uv run pytest \
  -o cache_dir=/tmp/vetpath-pytest-cache \
  tests/ -v
```

Run the code-quality check:

```bash
uv run ruff check . --no-cache
```

## Data and Safety Boundaries

VetPath is designed as a read-only information service.

The demonstrated prototype:

- Does not write to Veteran records.
- Does not determine individual eligibility.
- Does not provide clinical, legal, or financial advice.
- Does not retrieve real Veteran records.
- Does not process protected health information.
- Uses curated transition-information catalogs.
- Returns structured status, error, and provenance fields.

## Validation Boundaries

The following capabilities were demonstrated:

- Local MCP server startup using `stdio`.
- Client initialization and protocol negotiation.
- Discovery of all four MCP tools.
- Automated tool and security-focused test cases.
- Successful DD214 terminology invocation.
- Structured responses with source provenance.
- Successful Databricks App build and startup.

The following have not been established:

- Successful remote ChatGPT OAuth integration.
- Production VA-network connectivity.
- Access to real Veteran information.
- Enterprise security authorization.
- A VA Authority to Operate.
- Approval for operational or clinical use.
- Production reliability or performance.

## Prototype Status

VetPath MCP is a GSA Hackathon proof of concept.

Publication of this repository does not constitute:

- VA production authorization.
- An Authority to Operate.
- Authorization to process Veteran records.
- Approval to use protected or sensitive information.
- Approval for operational, benefits, healthcare, legal, or financial decision-making.

Any future operational use would require the applicable mission-owner, security, privacy, accessibility, records-management, AI-governance, and production-authorization reviews.

## License

This project is licensed under the terms included in the repository's `LICENSE` file.
