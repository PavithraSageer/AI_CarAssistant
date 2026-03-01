"""Pydantic schemas for API validation and response formatting."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SLAFields(BaseModel):
    """Schema representing the required SLA fields from the LLM output."""

    apr: str = Field(default="")
    loan_term: str = Field(default="")
    monthly_payment: str = Field(default="")
    total_payment: str = Field(default="")
    due_date: str = Field(default="")
    lender_name: str = Field(default="")
    borrower_name: str = Field(default="")
    vin: str = Field(default="")


class UploadContractResponse(BaseModel):
    """Response schema returned after OCR upload processing."""

    document_id: int
    filename: str
    extracted_text: str
    upload_timestamp: datetime


class SLAExtractionResponse(BaseModel):
    """Response schema returned after LLM SLA extraction."""

    document_id: int
    sla_data: SLAFields


class VehicleDetailsResponse(BaseModel):
    """Response schema for normalized NHTSA VIN lookup details."""

    vin: str
    make: str
    model: str
    model_year: str
    recalls: Any = None
