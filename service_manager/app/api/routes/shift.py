# app/api/routes/shift_router.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.controller.shift_controller import ShiftController
from app.api.schemas.schemas import ShiftCreate, ShiftRead
from common_utils.auth.permission_checker import PermissionChecker
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
controller = ShiftController()

@router.post("/", response_model=ShiftRead)
async def create_shift(
    shift: ShiftCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["shift_management.create"]))
):
    tenant_id = token_data["tenant_id"]
    return controller.create_shift(db, tenant_id, shift)

@router.get("/", response_model=List[ShiftRead])
async def fetch_shifts(
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["shift_management.read"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500)
):
    tenant_id = token_data["tenant_id"]
    logger.info(f"Fetching shifts for tenant_id={tenant_id}, skip={skip}, limit={limit}")

    try:
        shifts = controller.get_shifts(db, tenant_id, skip, limit)
        if not shifts:
            logger.warning(f"No shifts found for tenant_id={tenant_id}")
            raise HTTPException(status_code=404, detail="No shifts found for this tenant.")
        return shifts
    except HTTPException as e:
        logger.error(f"HTTP error while fetching shifts: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("Unexpected error while fetching shifts")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/{shift_id}", response_model=ShiftRead)
async def fetch_shift_by_id(
    shift_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["shift_management.read"]))
):
    tenant_id = token_data["tenant_id"]
    try:
        shift = controller.get_shift_by_id(db, tenant_id, shift_id)
        return shift
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error fetching shift id={shift_id} for tenant={tenant_id}")
        raise HTTPException(status_code=500, detail="Internal server error")