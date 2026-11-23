"""Retrieve one verified Veteran transition resource by catalog ID."""

from __future__ import annotations

from fastmcp import FastMCP

from vetpath_mcp.tools.search_veteran_resources import (
    catalog_provenance,
    load_catalog,
)
from vetpath_mcp.vetpath_models import (
    ProgramDetailsData,
    ResourceRecord,
    ResponseStatus,
    VetPathResponse,
)


def lookup_program(program_id: str) -> dict:
    """Retrieve a normalized resource without determining eligibility."""
    cleaned_id = program_id.strip()
    catalog = load_catalog()
    provenance = catalog_provenance(catalog)
    data = ProgramDetailsData(resource=None)

    if not cleaned_id or len(cleaned_id) > 100:
        return VetPathResponse[ProgramDetailsData](
            status=ResponseStatus.INVALID_INPUT,
            data=data,
            errors=["Program ID must be 1-100 characters."],
            provenance=provenance,
        ).model_dump(mode="json")

    for item in catalog["resources"]:
        if item["resource_id"].casefold() == cleaned_id.casefold():
            data.resource = ResourceRecord.model_validate(item)

            return VetPathResponse[ProgramDetailsData](
                status=ResponseStatus.SUCCESS,
                data=data,
                provenance=provenance,
            ).model_dump(mode="json")

    return VetPathResponse[ProgramDetailsData](
        status=ResponseStatus.NOT_FOUND,
        data=data,
        errors=[
            (
                "Program ID was not found. Use "
                "search_veteran_resources to find a valid ID."
            )
        ],
        provenance=provenance,
    ).model_dump(mode="json")


def register(mcp: FastMCP) -> None:
    """Register the program-details tool."""

    @mcp.tool(
        name="get_program_details",
        annotations={
            "title": "Get Veteran Program Details",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def get_program_details(program_id: str) -> dict:
        """Return one verified federal resource by catalog ID.

        Use search_veteran_resources first when the resource ID is
        unknown. This tool does not determine individual eligibility.
        """
        return lookup_program(program_id)
