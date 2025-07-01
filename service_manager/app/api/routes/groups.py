from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import GroupCreate, GroupRead, AssignPolicyRequest
from app.controller.group_controller import GroupController
from common_utils.auth.permission_checker import PermissionChecker

router = APIRouter()
group_controller = GroupController()

@router.post("/", response_model=GroupRead)
async def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["group_management.create"]))
):
    try:
        return group_controller.create_group(group, db)
    except HTTPException as e:
        raise e

@router.get("/", response_model=list[GroupRead])
def get_groups(
    token: dict = Depends(PermissionChecker(["group_management.read"])),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return group_controller.get_groups(db, skip=skip, limit=limit)

@router.get("/{group_id}", response_model=GroupRead)
def get_group(
    group_id: int,
    token: dict = Depends(PermissionChecker(["group_management.read"])),
    db: Session = Depends(get_db)
):
    return group_controller.get_group(group_id, db)

@router.post("/assign_policy")
def assign_policy(
    req: AssignPolicyRequest,
    token: dict = Depends(PermissionChecker(["group_management.update"])),
    db: Session = Depends(get_db)
):
    return group_controller.assign_policy(req, db)

@router.post("/remove_policy")
def remove_policy(
    req: AssignPolicyRequest,
    token: dict = Depends(PermissionChecker(["group_management.update"])),
    db: Session = Depends(get_db)
):
    return group_controller.remove_policy(req, db)

@router.put("/{group_id}", response_model=GroupRead)
def update_group(
    group_id: int,
    group_update: GroupCreate,
    token: dict = Depends(PermissionChecker(["group_management.update"])),
    db: Session = Depends(get_db)
):
    return group_controller.update_group(group_id, group_update, db)

@router.patch("/{group_id}", response_model=GroupRead)
def patch_group(
    group_id: int,
    group_update: dict,
    token: dict = Depends(PermissionChecker(["group_management.update"])),
    db: Session = Depends(get_db)
):
    return group_controller.patch_group(group_id, group_update, db)

@router.delete("/{group_id}", response_model=GroupRead)
def delete_group(
    group_id: int,
    token: dict = Depends(PermissionChecker(["group_management.delete"])),
    db: Session = Depends(get_db)
):
    return group_controller.delete_group(group_id, db)

@router.post("/{group_id}/users/{user_id}")
async def add_user_to_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["group_management.update"]))
):
    try:
        return group_controller.add_user_to_group(group_id, user_id, db)
    except HTTPException as e:
        raise e

@router.delete("/{group_id}/users/{user_id}")
async def remove_user_from_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["group_management.update"]))
):
    try:
        return group_controller.remove_user_from_group(group_id, user_id, db)
    except HTTPException as e:
        raise e