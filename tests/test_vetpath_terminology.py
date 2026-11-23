"""VetPath glossary contract and MCP integration tests."""

from __future__ import annotations

import asyncio

from fastmcp import Client

from vetpath_mcp.app import mcp
from vetpath_mcp.tools.resolve_military_terminology import resolve_term
from vetpath_mcp.vetpath_models import (
    TermResolutionData,
    VetPathResponse,
)


def test_bdd_expands_and_cites_official_source():
    response = resolve_term("BDD")

    assert response["status"] == "resolved"
    assert (
        response["data"]["interpretations"][0]["preferred_label"]
        == "Benefits Delivery at Discharge"
    )
    assert response["data"]["interpretations"][0]["source_url"].startswith(
        "https://www.va.gov/"
    )

    validated = VetPathResponse[TermResolutionData].model_validate(response)
    assert validated.schema_version == "0.2.0"


def test_common_response_envelope_includes_provenance():
    response = resolve_term("BDD")

    assert set(response) == {
        "schema_version",
        "status",
        "data",
        "errors",
        "provenance",
    }
    assert response["provenance"]
    assert response["provenance"][0]["source_type"] == ("official_federal_source")
    assert response["provenance"][0]["source_url"].startswith("https://www.va.gov/")


def test_case_insensitive_alias():
    response = resolve_term("vr&e")

    assert response["status"] == "resolved"
    assert response["data"]["interpretations"][0]["concept_id"] == "employment.vre"


def test_m2va_resolution():
    response = resolve_term("M2VA")

    assert response["status"] == "resolved"
    assert response["data"]["interpretations"][0]["domain"] == "healthcare"


def test_ambiguous_coe_requires_context():
    response = resolve_term("COE")

    assert response["status"] == "needs_context"
    assert response["data"]["requires_clarification"] is True


def test_coe_with_context():
    response = resolve_term(
        "COE",
        "I need a VA home loan for a mortgage",
    )

    assert response["status"] == "resolved"
    assert (
        response["data"]["interpretations"][0]["concept_id"]
        == "housing.va_home_loan_coe"
    )


def test_unknown_term_not_fabricated():
    response = resolve_term("ZZZNOTREAL")

    assert response["status"] == "not_found"
    assert response["data"]["interpretations"] == []


def test_invalid_input():
    response = resolve_term(" " * 4)

    assert response["status"] == "invalid_input"
    assert response["errors"]


def test_mcp_tool_is_callable():
    async def run():
        async with Client(mcp) as client:
            tools = await client.list_tools()

            assert "resolve_military_terminology" in {tool.name for tool in tools}

            result = await client.call_tool(
                "resolve_military_terminology",
                {"term": "PCPG"},
            )

            assert not result.is_error
            assert result.data["status"] == "resolved"

    asyncio.run(run())
