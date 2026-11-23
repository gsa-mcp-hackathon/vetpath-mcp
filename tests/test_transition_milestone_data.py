"""Validate the source-grounded VetPath milestone catalog."""

from __future__ import annotations

import json
from pathlib import Path

from vetpath_mcp.vetpath_models import (
    MilestoneRecord,
    TransitionPhase,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "src" / "vetpath_mcp" / "data"


def load_json(name: str) -> dict:
    path = DATA_DIR / name

    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_milestone_catalog_metadata():
    catalog = load_json("transition_milestones.json")

    assert catalog["catalog_version"] == "0.1.0"
    assert catalog["source_version"] == "1"
    assert len(catalog["milestones"]) == 17


def test_all_milestones_validate_against_shared_model():
    catalog = load_json("transition_milestones.json")

    validated = [MilestoneRecord.model_validate(item) for item in catalog["milestones"]]

    assert len(validated) == len(catalog["milestones"])


def test_milestone_ids_are_unique():
    catalog = load_json("transition_milestones.json")
    milestone_ids = [item["milestone_id"] for item in catalog["milestones"]]

    assert len(milestone_ids) == len(set(milestone_ids))


def test_all_controlled_phases_are_represented():
    catalog = load_json("transition_milestones.json")
    observed = {item["transition_phase"] for item in catalog["milestones"]}
    expected = {phase.value for phase in TransitionPhase}

    assert observed == expected


def test_related_resource_ids_exist():
    milestones = load_json("transition_milestones.json")
    resources = load_json("resources.json")

    resource_ids = {item["resource_id"] for item in resources["resources"]}

    referenced_ids = {
        resource_id
        for item in milestones["milestones"]
        for resource_id in item["related_resource_ids"]
    }

    assert referenced_ids <= resource_ids


def test_terminology_resource_ids_exist():
    terminology = load_json("terminology.json")
    resources = load_json("resources.json")

    resource_ids = {item["resource_id"] for item in resources["resources"]}

    referenced_ids = {
        resource_id
        for term in terminology["terms"]
        for resource_id in term["related_resource_ids"]
    }

    assert referenced_ids <= resource_ids


def test_healthcare_milestone_preserves_source_timing():
    catalog = load_json("transition_milestones.json")
    milestone = next(
        item
        for item in catalog["milestones"]
        if item["milestone_id"] == "apply-va-health-care"
    )

    assert milestone["transition_phase"] == (
        "three_months_before_to_three_months_after"
    )
    assert milestone["source_timing"] == "3 months before separation"
    assert "no general deadline" in milestone["important_note"].lower()


def test_solid_start_milestone_preserves_contact_points():
    catalog = load_json("transition_milestones.json")
    milestone = next(
        item
        for item in catalog["milestones"]
        if item["milestone_id"] == "engage-va-solid-start"
    )

    assert milestone["source_timing"] == ("90, 180, and 365 days after separation")
    assert milestone["related_resource_ids"] == ["va-solid-start"]


def test_every_milestone_has_source_and_review_metadata():
    catalog = load_json("transition_milestones.json")

    for milestone in catalog["milestones"]:
        assert milestone["source_document"]
        assert milestone["source_version"] == "1"
        assert milestone["source_page"] >= 1
        assert milestone["last_reviewed"]
        assert milestone["verification_status"] == "verified_official_source"
