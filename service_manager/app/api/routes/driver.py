# app/api/routes/driver.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.schemas.schemas import DriverCreate, DriverOut
from app.controller.driver_controller import DriverController
from app.database.database import get_db
from common_utils.auth.permission_checker import PermissionChecker

router = APIRouter()
controller = DriverController()

@router.post("/", response_model=DriverOut)
async def create_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["driver_management.create"]))
):
    # tenant_id = token_data["tenant_id"]
    try:
        return controller.create_driver(db, driver)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unexpected error while creating driver")