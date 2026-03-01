"""Router for contract upload and OCR extraction."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from database import get_db
from models import ContractDocument
from schemas import UploadContractResponse
from services.ocr_service import extract_text_from_upload, validate_upload_file

router = APIRouter(tags=["Upload"])
logger = logging.getLogger(__name__)


@router.post("/upload-contract", response_model=UploadContractResponse)
async def upload_contract(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a contract file, run OCR, store text, and return extraction output."""
    try:
        # Validate file type early to avoid expensive OCR work on unsupported files.
        validate_upload_file(file)

        # Read uploaded bytes asynchronously because UploadFile uses async file I/O.
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        # OCR execution is CPU-heavy, so move it to a threadpool to keep API responsive.
        extracted_text = await run_in_threadpool(extract_text_from_upload, file_bytes, file.filename)

        # Persist OCR results for downstream SLA extraction.
        document = ContractDocument(filename=file.filename or "unknown", extracted_text=extracted_text)
        db.add(document)
        db.commit()
        db.refresh(document)

        return UploadContractResponse(
            document_id=document.id,
            filename=document.filename,
            extracted_text=document.extracted_text,
            upload_timestamp=document.upload_timestamp,
        )
    except ValueError as error:
        logger.error("Upload validation/processing error: %s", error)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except HTTPException:
        # Re-raise FastAPI HTTP errors as-is.
        raise
    except Exception as error:
        logger.exception("Unexpected error during contract upload")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded contract.",
        ) from error
