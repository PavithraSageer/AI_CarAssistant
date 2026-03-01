"""Router for VIN-based vehicle details using NHTSA API."""

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from schemas import VehicleDetailsResponse
from services.vin_service import get_vehicle_details

router = APIRouter(tags=["Vehicle"])
logger = logging.getLogger(__name__)


@router.get("/vehicle-details/{vin}", response_model=VehicleDetailsResponse)
async def vehicle_details(vin: str):
    """Lookup and return vehicle details for a VIN from NHTSA."""
    try:
        # Run synchronous HTTP request in threadpool to avoid blocking event loop.
        details = await run_in_threadpool(get_vehicle_details, vin)
        return VehicleDetailsResponse(**details)
    except ValueError as error:
        logger.error("VIN validation/lookup error: %s", error)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected VIN lookup error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch vehicle details.",
        ) from error
