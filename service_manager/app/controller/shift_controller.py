# app/controller/shift_controller.py

from app.api.schemas.schemas import ShiftCreate
from app.crud.crud import create_shift, get_shift_by_id, get_shifts
from sqlalchemy.orm import Session

class ShiftController:
    def create_shift(self, db: Session, tenant_id: int, shift_data: ShiftCreate):
        return create_shift(db, tenant_id, shift_data)

    def get_shifts(self, db: Session, tenant_id: int, skip: int = 0, limit: int = 100):
        return get_shifts(db, tenant_id, skip, limit)
    
    def get_shift_by_id(self, db: Session, tenant_id: int, shift_id: int):
        return get_shift_by_id(db, tenant_id, shift_id)