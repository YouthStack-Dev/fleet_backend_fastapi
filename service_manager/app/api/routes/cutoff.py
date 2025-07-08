# app/api/routes/cutoff_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.controller.cutoff_controller import CutoffController
from app.api.schemas.schemas import CutoffCreate, CutoffRead, CutoffUpdate
from common_utils.auth.permission_checker import PermissionChecker

router = APIRouter()
controller = CutoffController()

@router.post("/", response_model=CutoffRead)
async def create_cutoff(
    cutoff: CutoffCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["cutoff.create"]))
):
    tenant_id = token_data["tenant_id"]
    return controller.create_cutoff(cutoff, db, tenant_id)


@router.get("/", response_model=CutoffRead)
async def get_cutoff(
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["cutoff.read"]))
):
    tenant_id = token_data["tenant_id"]
    result = controller.get_cutoff(db, tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Cutoff not found")
    return result


@router.put("/", response_model=CutoffRead)
async def update_cutoff(
    cutoff_update: CutoffUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["cutoff.update"]))
):
    tenant_id = token_data["tenant_id"]
    updated = controller.update_cutoff(tenant_id, cutoff_update, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Cutoff not found")
    return updated
