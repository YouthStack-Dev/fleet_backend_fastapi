from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import UserCreate, UserRead
from app.controller.user_controller import UserController
from common_utils.auth.permission_checker import PermissionChecker
from common_utils.auth.utils import hash_password

router = APIRouter()
user_controller = UserController()


@router.post("/", response_model=UserRead)
async def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db),  
    token_data: dict = Depends(PermissionChecker(["user_management.create"]))
):
    try:
        user.hashed_password = hash_password(user.hashed_password)
        return user_controller.create_user(user, db)
    except HTTPException as e:
        raise e


@router.get("/", response_model=list[UserRead])
def get_users(
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["user_management.read"])),
    skip: int = 0,
    limit: int = 100
):
    return user_controller.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["user_management.read"]))
):
    return user_controller.get_user(user_id, db)

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["user_management.update"]))
):
    return user_controller.update_user(user_id, user_update, db)

@router.patch("/{user_id}", response_model=UserRead)
def patch_user(
    user_id: int,
    user_update: dict,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["user_management.update"]))
):
    return user_controller.patch_user(user_id, user_update, db)

@router.delete("/{user_id}", response_model=UserRead)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["user_management.delete"]))
):
    return user_controller.delete_user(user_id, db)
