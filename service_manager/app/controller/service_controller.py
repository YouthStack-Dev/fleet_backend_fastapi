from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.api.schemas.schemas import ServiceCreate
from app.crud import crud

class ServiceController:
    def create_service(self, service: ServiceCreate, db: Session):
        return crud.create_service(db, service)

    def get_services(self, db: Session, skip: int = 0, limit: int = 100):
        return crud.get_services(db, skip=skip, limit=limit)

    def get_service(self, service_id: int, db: Session):
        service = crud.get_service(db, service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service

    def update_service(self, service_id: int, service_update: ServiceCreate, db: Session):
        updated = crud.update_service(db, service_id, service_update)
        if not updated:
            raise HTTPException(status_code=404, detail="Service not found")
        return updated

    def patch_service(self, service_id: int, service_update: dict, db: Session):
        updated = crud.patch_service(db, service_id, service_update)
        if not updated:
            raise HTTPException(status_code=404, detail="Service not found")
        return updated

    def delete_service(self, service_id: int, db: Session):
        deleted = crud.delete_service(db, service_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Service not found")
        return deleted
