# app/controller/vehicle_type_controller.py

from typing import Optional
from app.crud.crud import create_vehicle_type, delete_vehicle_type, get_vehicle_type_by_id,  get_vehicle_types_filtered, update_vehicle_type
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.api.schemas.schemas import VehicleTypeCreate, VehicleTypeUpdate

class VehicleTypeController:
    def create_vehicle_type(self, db: Session, payload: VehicleTypeCreate):
        try:
            return create_vehicle_type(db, payload)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error")
    def get_vehicle_type_by_id(self, db: Session, vehicle_type_id: int):
        try:
            return get_vehicle_type_by_id(db, vehicle_type_id)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Internal Server Error")

        
    def get_vehicle_types(self, db: Session, tenant_id: int, vendor_id: Optional[int], skip: int, limit: int):
        try:
            return get_vehicle_types_filtered(db, tenant_id, vendor_id, skip, limit)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Internal Server Error")
    def update_vehicle_type(self, db: Session, vehicle_type_id: int, payload: VehicleTypeUpdate):
        try:
            return update_vehicle_type(db, vehicle_type_id, payload)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Internal Server Error")
        
    def delete_vehicle_type(self, db: Session, vehicle_type_id: int):
        try:
            return delete_vehicle_type(db, vehicle_type_id)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Internal Server Error")