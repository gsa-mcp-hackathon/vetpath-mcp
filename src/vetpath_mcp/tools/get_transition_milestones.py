"""Retrieve source-grounded military transition milestones."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastmcp import FastMCP

from vetpath_mcp.vetpath_models import (
    MilestoneRecord,
    ProvenanceRecord,
    ResponseStatus,
    ServiceCategory,
    TransitionMilestoneData,
    TransitionPhase,
    VetPathResponse,
)

CATALOG = Path(__file__).resolve().parents[1] / "data" / "transition_milestones.json"


@lru_cache(maxsize=1)
def load_milestone_catalog() -> dict:
    """Load the reviewed milestone catalog once per process."""
    with CATALOG.open(encoding="utf-8") as handle:
        return json.load(handle)


def _coerce_phase(
    value: TransitionPhase | str,
) -> TransitionPhase | None:
    if isinstance(value, TransitionPhase):
        return value

    try:
        return TransitionPhase(str(value).strip())
    except ValueError:
        return None


def _coerce_category(
    value: ServiceCategory | str | None,
) -> ServiceCategory | None:
    if value is None or str(value).strip() == "":
        return None

    if isinstance(value, ServiceCategory):
        return value

    try:
        return ServiceCategory(str(value).strip())
    except ValueError:
        return None


def _catalog_provenance(
    catalog: dict,
    items: list[MilestoneRecord],
) -> list[ProvenanceRecord]:
    """Create catalog-level or page-level provenance records."""
    pages = sorted({item.source_page for item in items})

    if not pages:
        return [
            ProvenanceRecord(
                source_type="official_va_transition_workbook",
                source_document=catalog["source_document"],
                catalog_version=catalog["catalog_version"],
                last_reviewed=catalog["reviewed_on"],
            )
        ]

    return [
        ProvenanceRecord(
            source_type="official_va_transition_workbook",
            source_document=catalog["source_document"],
            source_page=page,
            catalog_version=catalog["catalog_version"],
            last_reviewed=catalog["reviewed_on"],
        )
        for page in pages
    ]


def lookup_transition_milestones(
    transition_phase: TransitionPhase | str,
    service_category: ServiceCategory | str | None = None,
    limit: int = 20,
) -> dict:
    """Retrieve reviewed milestones for one controlled phase."""
    catalog = load_milestone_catalog()

    requested_phase = (
        transition_phase.value
        if isinstance(transition_phase, TransitionPhase)
        else str(transition_phase).strip()
    )

    data = TransitionMilestoneData(
        requested_phase=requested_phase,
    )

    base_provenance = _catalog_provenance(catalog, [])
    phase = _coerce_phase(transition_phase)

    if phase is None:
        valid_phases = ", ".join(item.value for item in TransitionPhase)

        return VetPathResponse[TransitionMilestoneData](
            status=ResponseStatus.INVALID_INPUT,
            data=data,
            errors=[f"Unknown transition phase. Valid values: {valid_phases}."],
            provenance=base_provenance,
        ).model_dump(mode="json")

    category = _coerce_category(service_category)

    if (
        service_category is not None
        and str(service_category).strip()
        and category is None
    ):
        valid_categories = ", ".join(item.value for item in ServiceCategory)

        return VetPathResponse[TransitionMilestoneData](
            status=ResponseStatus.INVALID_INPUT,
            data=data,
            errors=[(f"Unknown service category. Valid values: {valid_categories}.")],
            provenance=base_provenance,
        ).model_dump(mode="json")

    if limit < 1 or limit > 50:
        return VetPathResponse[TransitionMilestoneData](
            status=ResponseStatus.INVALID_INPUT,
            data=data,
            errors=["Limit must be between 1 and 50."],
            provenance=base_provenance,
        ).model_dump(mode="json")

    data.transition_phase = phase
    data.service_category = category

    matches = []

    for item in catalog["milestones"]:
        if item["transition_phase"] != phase.value:
            continue

        if category is not None and category.value not in item["service_categories"]:
            continue

        matches.append(MilestoneRecord.model_validate(item))

    matches.sort(
        key=lambda item: (
            item.source_page,
            item.milestone_id,
        )
    )

    data.total_matches = len(matches)
    data.items = matches[:limit]
    provenance = _catalog_provenance(catalog, data.items)

    if not data.items:
        return VetPathResponse[TransitionMilestoneData](
            status=ResponseStatus.NOT_FOUND,
            data=data,
            errors=[
                (
                    "No reviewed milestone matched the supplied phase "
                    "and service category."
                )
            ],
            provenance=provenance,
        ).model_dump(mode="json")

    return VetPathResponse[TransitionMilestoneData](
        status=ResponseStatus.SUCCESS,
        data=data,
        provenance=provenance,
    ).model_dump(mode="json")


def register(mcp: FastMCP) -> None:
    """Register transition milestone retrieval."""

    @mcp.tool(
        name="get_transition_milestones",
        annotations={
            "title": "Get Veteran Transition Milestones",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def get_transition_milestones(
        transition_phase: TransitionPhase,
        service_category: ServiceCategory | None = None,
        limit: int = 20,
    ) -> dict:
        """Return reviewed actions for one transition phase.

        Optionally filter by service category. Results preserve the
        source workbook timing, page provenance, next steps, and scope
        limitations. This tool does not determine individual eligibility
        or calculate legal deadlines.
        """
        return lookup_transition_milestones(
            transition_phase,
            service_category,
            limit,
        )
