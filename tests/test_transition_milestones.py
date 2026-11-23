"""VetPath timeline retrieval and MCP integration tests."""

from __future__ import annotations

import asyncio

from fastmcp import Client

from vetpath_mcp.app import mcp
from vetpath_mcp.tools.get_transition_milestones import (
    lookup_transition_milestones,
)
from vetpath_mcp.vetpath_models import (
    TransitionMilestoneData,
    VetPathResponse,
)


def test_first_phase_returns_reviewed_milestones():
    response = lookup_transition_milestones("twelve_to_nine_months_before")

    assert response["status"] == "success"
    assert response["data"]["total_matches"] == 2
    assert len(response["data"]["items"]) == 2

    validated = VetPathResponse[TransitionMilestoneData].model_validate(response)

    assert validated.schema_version == "0.2.0"


def test_healthcare_filter_returns_expected_milestone():
    response = lookup_transition_milestones(
        "three_months_before_to_three_months_after",
        "healthcare",
    )

    assert response["status"] == "success"
    assert response["data"]["total_matches"] == 1
    assert response["data"]["items"][0]["milestone_id"] == "apply-va-health-care"


def test_unknown_phase_is_invalid_input():
    response = lookup_transition_milestones("not_a_real_transition_phase")

    assert response["status"] == "invalid_input"
    assert response["data"]["items"] == []
    assert response["errors"]


def test_unknown_category_is_invalid_input():
    response = lookup_transition_milestones(
        "nine_to_three_months_before",
        "not_a_real_category",
    )

    assert response["status"] == "invalid_input"
    assert response["errors"]


def test_valid_phase_without_category_match_is_not_found():
    response = lookup_transition_milestones(
        "twelve_to_nine_months_before",
        "housing",
    )

    assert response["status"] == "not_found"
    assert response["data"]["total_matches"] == 0
    assert response["data"]["items"] == []


def test_limit_preserves_total_match_count():
    response = lookup_transition_milestones(
        "nine_to_three_months_before",
        limit=1,
    )

    assert response["status"] == "success"
    assert response["data"]["total_matches"] == 6
    assert len(response["data"]["items"]) == 1


def test_successful_result_includes_page_provenance():
    response = lookup_transition_milestones("twelve_months_after_and_beyond")

    assert response["status"] == "success"
    assert response["provenance"]

    pages = {item["source_page"] for item in response["provenance"]}

    assert pages == {15}


def test_transition_tool_is_discoverable_and_callable():
    async def run():
        async with Client(mcp) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools}

            assert "get_transition_milestones" in names

            result = await client.call_tool(
                "get_transition_milestones",
                {
                    "transition_phase": ("nine_to_three_months_before"),
                    "service_category": "healthcare",
                },
            )

            assert not result.is_error
            assert result.data["status"] == "success"
            assert (
                result.data["data"]["items"][0]["milestone_id"]
                == "contact-va-healthcare-liaison"
            )

    asyncio.run(run())
