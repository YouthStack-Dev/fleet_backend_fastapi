# app/controller/shift_controller.py

from app.api.schemas.schemas import ShiftCreate
from app.crud.crud import create_shift
from sqlalchemy.orm import Session

class ShiftController:
    def create_shift(self, db: Session, tenant_id: int, shift_data: ShiftCreate):
        return create_shift(db, tenant_id, shift_data)
