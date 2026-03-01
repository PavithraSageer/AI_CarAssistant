"""SQLAlchemy database models for documents and SLA extraction results."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class ContractDocument(Base):
    """Stores uploaded contract metadata and OCR text content."""

    __tablename__ = "contract_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    extracted_text = Column(Text, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # One document can have one SLA extraction record.
    sla_result = relationship("SLAExtraction", back_populates="document", uselist=False)


class SLAExtraction(Base):
    """Stores normalized SLA fields extracted by the LLM."""

    __tablename__ = "sla_extractions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("contract_documents.id"), nullable=False, unique=True)
    extracted_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Back-reference to the source contract document.
    document = relationship("ContractDocument", back_populates="sla_result")
