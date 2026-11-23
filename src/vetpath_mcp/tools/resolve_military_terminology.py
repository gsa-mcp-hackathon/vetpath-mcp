"""Deterministic, source-backed military and VA terminology resolution."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastmcp import FastMCP

from vetpath_mcp.vetpath_models import (
    ProvenanceRecord,
    ResponseStatus,
    TermInterpretation,
    TermResolutionData,
    VetPathResponse,
)

_CATALOG = Path(__file__).resolve().parents[1] / "data" / "terminology.json"


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    with _CATALOG.open(encoding="utf-8") as handle:
        return json.load(handle)


def _catalog_provenance(
    catalog: dict,
    matches: list[dict],
) -> list[ProvenanceRecord]:
    """Create provenance records for the catalog and matched sources."""
    source_urls = sorted({item["source_url"] for item in matches})

    if not source_urls:
        return [
            ProvenanceRecord(
                source_type="curated_official_glossary",
                catalog_version=catalog["catalog_version"],
                last_reviewed=catalog["reviewed_on"],
            )
        ]

    return [
        ProvenanceRecord(
            source_type="official_federal_source",
            source_url=source_url,
            catalog_version=catalog["catalog_version"],
            last_reviewed=catalog["reviewed_on"],
        )
        for source_url in source_urls
    ]


def resolve_term(
    term: str,
    context: str = "",
    branch: str = "",
) -> dict:
    """Resolve a named term without inventing unknown definitions.

    General context is not retained, echoed, or logged by this tool.
    """
    original = term.strip()
    data = TermResolutionData(original_term=original)
    catalog = _load_catalog()
    catalog_provenance = _catalog_provenance(catalog, [])

    if not original or len(original) > 100 or len(context) > 300 or len(branch) > 50:
        return VetPathResponse[TermResolutionData](
            status=ResponseStatus.INVALID_INPUT,
            data=data,
            errors=["Term must be 1-100 characters; context <=300; branch <=50."],
            provenance=catalog_provenance,
        ).model_dump(mode="json")

    normalized = original.casefold()

    matches = [
        item
        for item in catalog["terms"]
        if normalized in {alias.casefold() for alias in item["aliases"]}
    ]

    if branch.strip():
        branch_name = branch.strip().casefold()
        matches = [
            item
            for item in matches
            if not item["branches"]
            or branch_name in {name.casefold() for name in item["branches"]}
        ]

    data.interpretations = [
        TermInterpretation(
            concept_id=item["concept_id"],
            preferred_label=item["preferred_label"],
            acronym=item["acronym"],
            definition=item["definition"],
            domain=item["domain"],
            related_resource_ids=item["related_resource_ids"],
            source_url=item["source_url"],
        )
        for item in matches
    ]

    provenance = _catalog_provenance(catalog, matches)

    if not matches:
        return VetPathResponse[TermResolutionData](
            status=ResponseStatus.NOT_FOUND,
            data=data,
            errors=[
                (
                    "Not in the verified catalog; ask for context "
                    "or refer to an official source."
                )
            ],
            provenance=provenance,
        ).model_dump(mode="json")

    context_normalized = context.casefold()

    unresolved = [
        item
        for item in matches
        if item["context_required"]
        and not any(
            keyword in context_normalized for keyword in item["context_keywords"]
        )
    ]

    if len(matches) > 1 or unresolved:
        data.requires_clarification = True

        return VetPathResponse[TermResolutionData](
            status=ResponseStatus.NEEDS_CONTEXT,
            data=data,
            errors=[
                (
                    "Please clarify the domain or intended meaning "
                    "before using this term."
                )
            ],
            provenance=provenance,
        ).model_dump(mode="json")

    return VetPathResponse[TermResolutionData](
        status=ResponseStatus.RESOLVED,
        data=data,
        provenance=provenance,
    ).model_dump(mode="json")


def register(mcp: FastMCP) -> None:
    """Register the military terminology resolver."""

    @mcp.tool(
        name="resolve_military_terminology",
        annotations={
            "title": "Resolve Military and VA Terminology",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def resolve_military_terminology(
        term: str,
        context: str = "",
        branch: str = "",
    ) -> dict:
        """Resolve a military or VA acronym with source attribution.

        Use a short term such as BDD or COE. Context distinguishes
        ambiguous meanings. Returns a common VetPath response envelope.
        No eligibility determinations, health advice, or live information
        are provided.
        """
        return resolve_term(term, context, branch)
