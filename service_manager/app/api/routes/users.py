from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import UserCreate, UserRead
from app.api.routes.auth import get_token_payload, token_dependency
from app.controller.user_controller import UserController

router = APIRouter()
user_controller = UserController()

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_controller.create_user(user, db)

@router.get("/", response_model=list[UserRead])
def get_users(
    token: token_dependency,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return user_controller.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return user_controller.get_user(user_id, db)

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserCreate,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return user_controller.update_user(user_id, user_update, db)

@router.patch("/{user_id}", response_model=UserRead)
def patch_user(
    user_id: int,
    user_update: dict,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return user_controller.patch_user(user_id, user_update, db)

@router.delete("/{user_id}", response_model=UserRead)
def delete_user(
    user_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return user_controller.delete_user(user_id, db)
