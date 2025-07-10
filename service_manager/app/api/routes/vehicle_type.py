from fastapi import APIRouter, Depends, HTTPException
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
