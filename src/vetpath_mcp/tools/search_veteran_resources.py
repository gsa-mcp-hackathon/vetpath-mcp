"""Search a curated catalog of official Veteran transition resources."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from fastmcp import FastMCP

from vetpath_mcp.vetpath_models import (
    ProvenanceRecord,
    ResourceRecord,
    ResourceSearchData,
    ResponseStatus,
    VetPathResponse,
)

CATALOG = Path(__file__).resolve().parents[1] / "data" / "resources.json"


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    """Load the reviewed resource catalog once per process."""
    with CATALOG.open(encoding="utf-8") as handle:
        return json.load(handle)


def catalog_provenance(catalog: dict) -> list[ProvenanceRecord]:
    """Return provenance for the curated resource catalog."""
    return [
        ProvenanceRecord(
            source_type="curated_official_resource_catalog",
            catalog_version=catalog["catalog_version"],
            last_reviewed=catalog["reviewed_on"],
        )
    ]


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9&]+", value.casefold())


def _as_resource(item: dict) -> ResourceRecord:
    return ResourceRecord.model_validate(item)


def search_catalog(query: str, limit: int = 5) -> dict:
    """Search official resources by controlled terms and aliases."""
    cleaned_query = query.strip()
    catalog = load_catalog()
    provenance = catalog_provenance(catalog)

    data = ResourceSearchData(
        query=cleaned_query,
        total_matches=0,
        items=[],
    )

    if not cleaned_query or len(cleaned_query) > 200 or limit < 1 or limit > 10:
        return VetPathResponse[ResourceSearchData](
            status=ResponseStatus.INVALID_INPUT,
            data=data,
            errors=["Query must be 1-200 characters and limit must be 1-10."],
            provenance=provenance,
        ).model_dump(mode="json")

    terms = _tokenize(cleaned_query)
    phrase = cleaned_query.casefold()
    matches: list[tuple[int, ResourceRecord]] = []

    for item in catalog["resources"]:
        resource = _as_resource(item)

        searchable = " ".join(
            [
                resource.resource_id,
                resource.preferred_name,
                resource.description,
                *[category.value for category in resource.service_categories],
                *resource.aliases,
                *resource.keywords,
            ]
        ).casefold()

        score = sum(term in searchable for term in terms)

        if phrase in searchable:
            score += 2

        if score > 0:
            matches.append((score, resource))

    matches.sort(
        key=lambda match: (
            -match[0],
            match[1].preferred_name.casefold(),
        )
    )

    data.total_matches = len(matches)
    data.items = [resource for _, resource in matches[:limit]]

    if not data.items:
        return VetPathResponse[ResourceSearchData](
            status=ResponseStatus.NOT_FOUND,
            data=data,
            errors=["No verified resource matched the supplied query."],
            provenance=provenance,
        ).model_dump(mode="json")

    return VetPathResponse[ResourceSearchData](
        status=ResponseStatus.SUCCESS,
        data=data,
        provenance=provenance,
    ).model_dump(mode="json")


def register(mcp: FastMCP) -> None:
    """Register the Veteran resource search tool."""

    @mcp.tool(
        name="search_veteran_resources",
        annotations={
            "title": "Search Veteran Resources",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def search_veteran_resources(
        query: str,
        limit: int = 5,
    ) -> dict:
        """Find verified public Veteran transition resources.

        Searches a curated catalog of official federal resources.
        Does not determine individual eligibility or provide clinical,
        legal, or financial advice.
        """
        return search_catalog(query, limit)
