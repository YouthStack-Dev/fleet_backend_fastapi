# app/controller/vehicle_type_controller.py

from app.crud.crud import create_vehicle_type
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.api.schemas.schemas import VehicleTypeCreate

class VehicleTypeController:
    def create_vehicle_type(self, db: Session, payload: VehicleTypeCreate):
        try:
            return create_vehicle_type(db, payload)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error")
