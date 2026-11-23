# VetPath Ontology v0.1 — terminology slice

## Purpose

Deterministic military and VA terminology lookup with explicit provenance,
controlled identifiers, and Pydantic response validation. This is a **lightweight
controlled vocabulary**, not a complete OWL/RDF ontology or official VA standard.

## Content

- `src/vetpath_mcp/data/terminology.json`: approved initial terms and aliases
- `src/vetpath_mcp/vetpath_models.py`: shared output schema
- `src/vetpath_mcp/tools/resolve_military_terminology.py`: MCP tool
- `tests/test_vetpath_terminology.py`: unit and MCP client tests

The public VA *Know Before You Go* workbook was a discovery/reference input.
We do not upload or copy the user-supplied SharePoint document. The term catalog
uses publicly available government URLs, and records a review date for this
**catalog**, not a guarantee that program details remain current.

## Response contract

All VetPath tools use the same outer response envelope:

- `schema_version`
- `status`
- `data`
- `errors`
- `provenance`

The shared envelope is generic, allowing each tool to provide its own
validated data model. Schema version `0.2.0` supports the current
terminology statuses plus reusable `success` and `error` statuses.

Terminology statuses include `resolved`, `needs_context`, `not_found`,
and `invalid_input`.

The resolver never infers entitlement, benefits eligibility, claim deadlines,
medical advice, or employment rights. A returned term is **not** an eligibility
assessment. `COE` illustrates ambiguity: context is required before assigning
the VA home loan meaning. Unknown terms (including ETS/EAS pending source
review) are not guessed.

Future work: add branch-specific terms, domain-sensitive multiple meanings,
relate terminology to transition milestones, and adopt the same response envelope
for the remaining resource tools. Do not log raw queries or personal information.
