"""Shared VetPath semantic response models."""

from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class ResponseStatus(str, Enum):
    """Supported statuses across VetPath MCP tools."""

    SUCCESS = "success"
    RESOLVED = "resolved"
    NEEDS_CONTEXT = "needs_context"
    NOT_FOUND = "not_found"
    INVALID_INPUT = "invalid_input"
    ERROR = "error"


class ServiceCategory(str, Enum):
    """Controlled categories for Veteran transition resources."""

    HEALTHCARE = "healthcare"
    MENTAL_HEALTH = "mental_health"
    DISABILITY = "disability"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    TRANSITION = "transition"
    HOUSING = "housing"


class TransitionPhase(str, Enum):
    """Controlled transition windows from the source workbook."""

    TWELVE_TO_NINE_MONTHS_BEFORE = "twelve_to_nine_months_before"
    NINE_TO_THREE_MONTHS_BEFORE = "nine_to_three_months_before"
    THREE_MONTHS_BEFORE_TO_THREE_MONTHS_AFTER = (
        "three_months_before_to_three_months_after"
    )
    THREE_TO_TWELVE_MONTHS_AFTER = "three_to_twelve_months_after"
    TWELVE_MONTHS_AFTER_AND_BEYOND = "twelve_months_after_and_beyond"


class ResourceType(str, Enum):
    """Controlled types for cataloged federal resources."""

    FEDERAL_PROGRAM = "federal_program"
    FEDERAL_BENEFIT = "federal_benefit"
    FEDERAL_SERVICE = "federal_service"


class VerificationStatus(str, Enum):
    """Review status for a catalog record."""

    VERIFIED_OFFICIAL_SOURCE = "verified_official_source"
    PENDING_REVIEW = "pending_review"


class EligibilityDetermination(str, Enum):
    """Eligibility state returned by the navigator."""

    NOT_ASSESSED = "not_assessed"


class ProvenanceRecord(BaseModel):
    """Source metadata supporting a VetPath result."""

    source_type: str
    source_url: str | None = None
    source_document: str | None = None
    source_page: int | None = Field(default=None, ge=1)
    catalog_version: str | None = None
    last_reviewed: str | None = None


class OfficialLink(BaseModel):
    """Authoritative link associated with a resource."""

    purpose: str
    url: str


class EligibilityNotice(BaseModel):
    """Explicitly prevent VetPath from implying eligibility."""

    determination: EligibilityDetermination = EligibilityDetermination.NOT_ASSESSED
    requires_official_verification: bool = True


class ResourceRecord(BaseModel):
    """Normalized federal transition resource."""

    resource_id: str
    preferred_name: str
    resource_type: ResourceType
    agency: str
    description: str
    service_categories: list[ServiceCategory]
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    official_links: list[OfficialLink]
    eligibility: EligibilityNotice = Field(default_factory=EligibilityNotice)
    verification_status: VerificationStatus
    last_reviewed: str


class ResourceSearchData(BaseModel):
    """Tool-specific data returned by resource search."""

    query: str
    total_matches: int = 0
    items: list[ResourceRecord] = Field(default_factory=list)


class ProgramDetailsData(BaseModel):
    """Tool-specific data returned for one program."""

    resource: ResourceRecord | None = None


class MilestoneRecord(BaseModel):
    """Source-grounded action in the military-to-civilian timeline."""

    milestone_id: str
    action: str
    transition_phase: TransitionPhase
    service_categories: list[ServiceCategory]
    related_resource_ids: list[str] = Field(default_factory=list)
    source_timing: str
    next_steps: list[str] = Field(default_factory=list)
    important_note: str | None = None
    source_document: str
    source_version: str
    source_page: int = Field(ge=1)
    verification_status: VerificationStatus
    last_reviewed: str


class TransitionMilestoneData(BaseModel):
    """Tool-specific data returned by milestone retrieval."""

    requested_phase: str
    transition_phase: TransitionPhase | None = None
    service_category: ServiceCategory | None = None
    total_matches: int = 0
    items: list[MilestoneRecord] = Field(default_factory=list)


class TermInterpretation(BaseModel):
    concept_id: str
    preferred_label: str
    acronym: str
    definition: str
    domain: str
    related_resource_ids: list[str] = Field(default_factory=list)
    source_url: str


class TermResolutionData(BaseModel):
    original_term: str
    interpretations: list[TermInterpretation] = Field(default_factory=list)
    requires_clarification: bool = False


DataT = TypeVar("DataT")


class VetPathResponse(BaseModel, Generic[DataT]):
    """Common VetPath response envelope with tool-specific typed data."""

    model_config = ConfigDict(use_enum_values=True)

    schema_version: str = "0.2.0"
    status: ResponseStatus
    data: DataT
    errors: list[str] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
