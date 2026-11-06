from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    """Source text supporting each extracted CRM field."""

    model_config = ConfigDict(extra="forbid")

    company: str | None = None
    contact: str | None = None
    stage: str | None = None
    next_step_date: str | None = None
    deal_value: str | None = None


class CRMExtraction(BaseModel):
    """Structured and validated output from the AI extractor."""

    model_config = ConfigDict(extra="forbid")

    company: str | None = None
    contact: str | None = None

    stage: Literal[
        "New",
        "Qualified",
        "Proposal",
        "Negotiation",
        "Won",
        "Lost",
    ] | None = None

    next_step: str | None = None
    next_step_date: date | None = None

    deal_value: float | None = Field(
        default=None,
        ge=0,
        description="Numeric deal value without currency conversion",
    )

    currency: str | None = Field(
        default=None,
        description="Currency code, for example INR or USD",
    )

    notes: str | None = None
    needs_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)

    evidence: Evidence


def validate_extraction(data: dict) -> CRMExtraction:
    """Validate AI output against the CRM schema."""
    return CRMExtraction.model_validate(data)