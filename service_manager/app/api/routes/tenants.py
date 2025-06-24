from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import TenantCreate, TenantRead, CompanyCreate, CompanyRead
from app.api.routes.auth import token_dependency
from app.controller.tenant_controller import TenantController

router = APIRouter()
tenant_controller = TenantController()

@router.post("/", response_model=TenantRead)
def create_tenant(
    tenant: TenantCreate,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return tenant_controller.create_tenant(tenant, db)

@router.get("/", response_model=list[TenantRead])
def get_tenants(
    token: token_dependency,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return tenant_controller.get_tenants(db, skip=skip, limit=limit)

@router.get("/{tenant_id}", response_model=TenantRead)
def get_tenant(
    tenant_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return tenant_controller.get_tenant(tenant_id, db)

@router.put("/{tenant_id}", response_model=TenantRead)
def update_tenant(
    tenant_id: int,
    tenant_update: TenantCreate,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return tenant_controller.update_tenant(tenant_id, tenant_update, db)

@router.patch("/{tenant_id}", response_model=TenantRead)
def patch_tenant(
    tenant_id: int,
    tenant_update: dict,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return tenant_controller.patch_tenant(tenant_id, tenant_update, db)

@router.delete("/{tenant_id}", response_model=TenantRead)
def delete_tenant(
    tenant_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return tenant_controller.delete_tenant(tenant_id, db)