# app/api/routes/shift_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.controller.shift_controller import ShiftController
from app.api.schemas.schemas import ShiftCreate, ShiftRead
from common_utils.auth.permission_checker import PermissionChecker

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
