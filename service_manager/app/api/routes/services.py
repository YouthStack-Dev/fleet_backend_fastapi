from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import ServiceCreate, ServiceRead
from app.controller.service_controller import ServiceController
from common_utils.auth.permission_checker import PermissionChecker
from typing import List
router = APIRouter()
service_controller = ServiceController()

@router.post("/", response_model=ServiceRead)
async def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["service_management.create"]))
):
    try:
        return service_controller.create_service(service, db)
    except HTTPException as e:
        raise e

@router.get("/", response_model=list[ServiceRead])
async def get_services(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["service_management.read"]))
):
    try:
        return service_controller.get_services(db, skip=skip, limit=limit)
    except HTTPException as e:
        raise e

@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["service_management.read"]))
):
    try:
        return service_controller.get_service(service_id, db)
    except HTTPException as e:
        raise e

@router.put("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: int,
    service_update: ServiceCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["service_management.update"]))
):
    try:
        return service_controller.update_service(service_id, service_update, db)
    except HTTPException as e:
        raise e

@router.patch("/{service_id}", response_model=ServiceRead)
async def patch_service(
    service_id: int,
    service_update: dict,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["service_management.update"]))
):
    try:
        return service_controller.patch_service(service_id, service_update, db)
    except HTTPException as e:
        raise e

@router.delete("/{service_id}", response_model=ServiceRead)
async def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["service_management.delete"]))
):
    try:
        return service_controller.delete_service(service_id, db)
    except HTTPException as e:
        raise e
    
@router.post("/seed", response_model=list[ServiceRead])
async def seed_services(
    db: Session = Depends(get_db),
    # token_data: dict = Depends(PermissionChecker(["service_management.create"]))
):
    try:
        return service_controller.seed_services(db)
    except HTTPException as e:
        raise e
