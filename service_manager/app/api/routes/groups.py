from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import GroupCreate, GroupRead, AssignPolicyRequest
from app.api.routes.auth import token_dependency
from app.controller.group_controller import GroupController

router = APIRouter()
group_controller = GroupController()

@router.post("/", response_model=GroupRead)
def create_group(
    group: GroupCreate,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return group_controller.create_group(group, db)

@router.get("/", response_model=list[GroupRead])
def get_groups(
    token: token_dependency,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return group_controller.get_groups(db, skip=skip, limit=limit)

@router.get("/{group_id}", response_model=GroupRead)
def get_group(
    group_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return group_controller.get_group(group_id, db)

@router.post("/assign_policy")
def assign_policy(
    req: AssignPolicyRequest,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return group_controller.assign_policy(req, db)

@router.post("/remove_policy")
def remove_policy(
    req: AssignPolicyRequest,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return group_controller.remove_policy(req, db)

@router.put("/{group_id}", response_model=GroupRead)
def update_group(
    group_id: int,
    group_update: GroupCreate,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return group_controller.update_group(group_id, group_update, db)

@router.patch("/{group_id}", response_model=GroupRead)
def patch_group(
    group_id: int,
    group_update: dict,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return group_controller.patch_group(group_id, group_update, db)

@router.delete("/{group_id}", response_model=GroupRead)
def delete_group(
    group_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return group_controller.delete_group(group_id, db)