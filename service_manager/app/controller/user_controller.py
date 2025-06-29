from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.api.schemas.schemas import UserCreate
from app.crud import crud

class UserController:
    def create_user(self, user: UserCreate, db: Session):
        try:
            return crud.create_user(db, user)
        except Exception as e:
            raise e
        
    def get_users(self, db: Session, skip: int = 0, limit: int = 100):
        return crud.get_users(db, skip=skip, limit=limit)

    def get_user(self, user_id: int, db: Session):
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def update_user(self, user_id: int, user_update: UserCreate, db: Session):
        updated = crud.update_user(db, user_id, user_update)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated

    def patch_user(self, user_id: int, user_update: dict, db: Session):
        updated = crud.patch_user(db, user_id, user_update)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated

    def delete_user(self, user_id: int, db: Session):
        deleted = crud.delete_user(db, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
        return deleted
