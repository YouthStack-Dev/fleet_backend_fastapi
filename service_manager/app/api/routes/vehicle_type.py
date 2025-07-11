from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException ,Path, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.controller.vehicle_type_controller import VehicleTypeController
from app.api.schemas.schemas import VehicleTypeCreate, VehicleTypeOut
from common_utils.auth.permission_checker import PermissionChecker

router = APIRouter()
controller = VehicleTypeController()

@router.post("/", response_model=VehicleTypeOut)
async def create_vehicle_type(
    payload: VehicleTypeCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vehicle_type_management.create"]))
):
    try:
        return controller.create_vehicle_type(db, payload)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{vehicle_type_id}", response_model=VehicleTypeOut)
async def get_vehicle_type_by_id(
    vehicle_type_id: int = Path(..., gt=0, description="ID of the vehicle type"),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vehicle_type_management.read"]))
):
    try:
        return controller.get_vehicle_type_by_id(db, vehicle_type_id)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/", response_model=List[VehicleTypeOut])
async def get_vehicle_types(
    vendor_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vehicle_type_management.read"]))
):
    tenant_id = token_data["tenant_id"]
    try:
        return controller.get_vehicle_types(db, tenant_id, vendor_id, skip, limit)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")