from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.controller.mapping_controller import MappingController
from common_utils.auth.permission_checker import PermissionChecker

router = APIRouter()
mapping_controller = MappingController()

@router.post("/user-tenant/{user_id}/{tenant_id}")
async def add_user_tenant(
    user_id: int,
    tenant_id: int,
    metadata: dict = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["mapping_management.create"]))
):
    try:
        return mapping_controller.add_user_tenant(user_id, tenant_id, metadata, db)
    except HTTPException as e:
        raise e

@router.get("/user_tenant/")
def list_user_tenants(
    token: dict = Depends(PermissionChecker(["mapping_management.read"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.list_user_tenants(db)

@router.delete("/user_tenant/")
def remove_user_tenant(
    user_id: int,
    tenant_id: int,
    token: dict = Depends(PermissionChecker(["mapping_management.delete"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.remove_user_tenant(user_id, tenant_id, db)

@router.post("/user-role/{user_id}/{role_id}/{tenant_id}")
async def add_user_role(
    user_id: int,
    role_id: int,
    tenant_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["mapping_management.create"]))
):
    try:
        return mapping_controller.add_user_role(user_id, role_id, tenant_id, db)
    except HTTPException as e:
        raise e

@router.get("/user_role/")
async def list_user_roles(
    token: dict = Depends(PermissionChecker(["mapping_management.read"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.list_user_roles(db)

@router.delete("/user_role/")
async def remove_user_role(
    user_id: int,
    role_id: int,
    tenant_id: int,
    token: dict = Depends(PermissionChecker(["mapping_management.delete"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.remove_user_role(user_id, role_id, tenant_id, db)

@router.post("/group-role/{group_id}/{role_id}")
async def add_group_role(
    group_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["mapping_management.create"]))
):
    try:
        return mapping_controller.add_group_role(group_id, role_id, db)
    except HTTPException as e:
        raise e

@router.get("/group_role/")
def list_group_roles(
    token: dict = Depends(PermissionChecker(["mapping_management.read"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.list_group_roles(db)

@router.delete("/group_role/")
def remove_group_role(
    group_id: int,
    role_id: int,
    token: dict = Depends(PermissionChecker(["mapping_management.delete"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.remove_group_role(group_id, role_id, db)

@router.post("/group_user/")
def add_group_user(
    group_id: int,
    user_id: int,
    token: dict = Depends(PermissionChecker(["mapping_management.create"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.add_group_user(group_id, user_id, db)

@router.get("/group_user/")
def list_group_users(
    token: dict = Depends(PermissionChecker(["mapping_management.read"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.list_group_users(db)

@router.delete("/group_user/")
def remove_group_user(
    group_id: int,
    user_id: int,
    token: dict = Depends(PermissionChecker(["mapping_management.delete"])),
    db: Session = Depends(get_db)
):
    return mapping_controller.remove_group_user(group_id, user_id, db)
