from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import ServiceCreate, ServiceRead
from app.api.routes.auth import token_dependency
from app.controller.service_controller import ServiceController

router = APIRouter()
service_controller = ServiceController()

@router.post("/", response_model=ServiceRead)
def create_service(
    service: ServiceCreate,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return service_controller.create_service(service, db)

@router.get("/", response_model=list[ServiceRead])
def get_services(
    token: token_dependency,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return service_controller.get_services(db, skip=skip, limit=limit)

@router.get("/{service_id}", response_model=ServiceRead)
def get_service(
    service_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return service_controller.get_service(service_id, db)

@router.put("/{service_id}", response_model=ServiceRead)
def update_service(
    service_id: int,
    service_update: ServiceCreate,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return service_controller.update_service(service_id, service_update, db)

@router.patch("/{service_id}", response_model=ServiceRead)
def patch_service(
    service_id: int,
    service_update: dict,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return service_controller.patch_service(service_id, service_update, db)

@router.delete("/{service_id}", response_model=ServiceRead)
def delete_service(
    service_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return service_controller.delete_service(service_id, db)