# add auth router
from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from psycopg2 import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import text  # Add this import at the top
import hashlib
import jwt
from app.database.database import get_db   
from app.api.schemas.schemas import (
    UserCreate, UserRead, LoginRequest, TokenResponse, ChangePasswordRequest
)
from app.crud import crud
from app.utils.policy_check import check_policy_access

router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user:
        print(f"User {username} not found")
        return None
    # Verify the hashed password
    if not crud.verify_password(hash_password(password), user.hashed_password):
        print(f"Password for user {username} is incorrect")
        return None
    return user

def create_access_token(data: dict, expires_delta: int = 3600):
    from datetime import datetime, timedelta
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")

def get_current_user(db: Session, token: str):
    from jose import jwt, JWTError
    from fastapi.security import OAuth2PasswordBearer
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
    
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = crud.get_user_by_username(db, username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
def get_token_payload(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        user_data = user.dict()
        user_data["hashed_password"] = hash_password(user_data["hashed_password"])
        return crud.create_user(db, UserCreate(**user_data))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists")
    
@router.post("/login", response_model=TokenResponse)
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Fetch roles from db
    roles = [
        r.name
        for r in db.execute(
            text("""
            SELECT roles.name FROM roles
            JOIN user_role ON roles.id = user_role.role_id
            WHERE user_role.user_id = :user_id
            """),
            {"user_id": user.id}
        ).fetchall()
    ] if user.id else []

    # Fetch policies from db
    policies = [
        {
            "id": row.id,
            "action": row.action,
            "resource": row.resource,
            "service_id": row.service_id,
            "tenant_id": row.tenant_id
        }
        for row in db.execute(
            text("""
            SELECT id, action, resource, service_id, tenant_id
            FROM policies
            WHERE user_id = :user_id
            """),
            {"user_id": user.id}
        ).fetchall()
    ] if user.id else []
    
    access_token = create_access_token(
        data={
            "sub": user.username,
            "roles": roles,
            "policies": policies
        }
    )
    return TokenResponse(access_token=access_token, token_type="bearer")

@router.post("/me")
def get_me(payload: dict = Depends(get_token_payload)):
    return payload

@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(get_token_payload)
):
    # Implement password change logic here
    return {"message": "Password change endpoint (protected)"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_token_dependency(token: Annotated[str, Depends(oauth2_scheme)], request: Request = None):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Policy check
    check_policy_access(payload, request)
    return token

token_dependency = Annotated[str, Depends(get_token_dependency)]
