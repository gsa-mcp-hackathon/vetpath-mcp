"""VetPath resource catalog and MCP integration tests."""

from __future__ import annotations

import asyncio

from fastmcp import Client

from vetpath_mcp.app import mcp
from vetpath_mcp.tools.get_program_details import lookup_program
from vetpath_mcp.tools.search_veteran_resources import search_catalog
from vetpath_mcp.vetpath_models import (
    ProgramDetailsData,
    ResourceSearchData,
    VetPathResponse,
)


def test_healthcare_search_returns_official_resource():
    response = search_catalog("health care")

    assert response["status"] == "success"
    assert response["data"]["total_matches"] >= 1
    assert response["data"]["items"][0]["resource_id"] == ("va-health-care")

    validated = VetPathResponse[ResourceSearchData].model_validate(response)
    assert validated.schema_version == "0.2.0"


def test_search_uses_aliases():
    response = search_catalog("GI Bill")

    assert response["status"] == "success"
    assert response["data"]["items"][0]["resource_id"] == ("va-education-benefits")


def test_home_loan_search():
    response = search_catalog("home loan COE")

    assert response["status"] == "success"
    assert response["data"]["items"][0]["resource_id"] == ("va-home-loan-coe")


def test_unknown_resource_search_is_not_found():
    response = search_catalog("ZZZNOTAREALRESOURCE")

    assert response["status"] == "not_found"
    assert response["data"]["items"] == []


def test_invalid_resource_search():
    response = search_catalog("", limit=5)

    assert response["status"] == "invalid_input"
    assert response["errors"]


def test_program_details_preserve_eligibility_boundary():
    response = lookup_program("va-vre")

    assert response["status"] == "success"
    assert response["data"]["resource"]["resource_id"] == "va-vre"
    assert (
        response["data"]["resource"]["eligibility"]["determination"] == "not_assessed"
    )
    assert (
        response["data"]["resource"]["eligibility"]["requires_official_verification"]
        is True
    )

    VetPathResponse[ProgramDetailsData].model_validate(response)


def test_unknown_program_id_is_not_found():
    response = lookup_program("not-a-real-program")

    assert response["status"] == "not_found"
    assert response["data"]["resource"] is None


def test_resource_tools_are_discoverable_and_callable():
    async def run():
        async with Client(mcp) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools}

            assert "search_veteran_resources" in names
            assert "get_program_details" in names

            search_result = await client.call_tool(
                "search_veteran_resources",
                {"query": "Solid Start"},
            )
            assert not search_result.is_error
            assert search_result.data["status"] == "success"

            details_result = await client.call_tool(
                "get_program_details",
                {"program_id": "va-solid-start"},
            )
            assert not details_result.is_error
            assert details_result.data["status"] == "success"

    asyncio.run(run())
