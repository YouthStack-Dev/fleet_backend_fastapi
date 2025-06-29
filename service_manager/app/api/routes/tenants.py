from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import TenantCreate, TenantRead
from app.controller.tenant_controller import TenantController
from common_utils.auth.permission_checker import PermissionChecker

router = APIRouter()
tenant_controller = TenantController()

@router.post("/", response_model=TenantRead)
async def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["tenant_management.create"]))
):
    try:
        return tenant_controller.create_tenant(tenant, db)
    except HTTPException as e:
        raise e

@router.get("/", response_model=list[TenantRead])
async def get_tenants(
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["tenant_management.read"])),
    skip: int = 0,
    limit: int = 100
):
    return tenant_controller.get_tenants(db, skip=skip, limit=limit)

@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["tenant_management.read"]))
):
    tenant = tenant_controller.get_tenant(tenant_id, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.put("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: int,
    tenant_update: TenantCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["tenant_management.update"]))
):
    tenant = tenant_controller.update_tenant(tenant_id, tenant_update, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.patch("/{tenant_id}", response_model=TenantRead)
async def patch_tenant(
    tenant_id: int,
    tenant_update: dict,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["tenant_management.update"]))
):
    tenant = tenant_controller.patch_tenant(tenant_id, tenant_update, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.delete("/{tenant_id}", response_model=TenantRead)
async def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["tenant_management.delete"]))
):
    tenant = tenant_controller.delete_tenant(tenant_id, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant