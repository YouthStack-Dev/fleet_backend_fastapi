# app/controller/cutoff_controller.py

from app.crud.crud import create_cutoff, get_cutoff_by_tenant, update_cutoff
from sqlalchemy.orm import Session
from app.api.schemas.schemas import CutoffCreate, CutoffUpdate

class CutoffController:
    def create_cutoff(self, cutoff: CutoffCreate, db: Session, tenant_id: int):
        return create_cutoff(db, cutoff, tenant_id)

    def get_cutoff(self, db: Session, tenant_id: int):
        return get_cutoff_by_tenant(db, tenant_id)

    def update_cutoff(self, tenant_id: int, cutoff_update: CutoffUpdate, db: Session):
        return update_cutoff(db, tenant_id, cutoff_update)
