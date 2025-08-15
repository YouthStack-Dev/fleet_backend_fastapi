from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.orm import Session
import os, secrets, json, time
from app.database.database import get_db   
from app.api.schemas.schemas import TokenResponse
from app.crud import crud
from common_utils.auth.utils import create_access_token, hash_password , verify_password
from common_utils.auth.permission_checker import PermissionChecker
from common_utils.auth.token_validation import Oauth2AsAccessor, validate_bearer_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controller.user_controller import UserController

security = HTTPBearer()
router = APIRouter()

# Token configuration
TOKEN_EXPIRY_HOURS = int(os.getenv("TOKEN_EXPIRY_HOURS", "1"))
X_INTROSPECT_SECRET = os.getenv("X_Introspect_Secret","Testing_").strip()

def authenticate_user(db: Session, email: str, password: str):
    user = crud.get_user_by_email(db, email)
    if not user:
        print(f"User with email {email} not found")
        return None
    if not verify_password(hash_password(password), user.hashed_password):
        print(f"Password for email {email} is incorrect")
        return None
    return user


@router.post("/introspect")
async def introspect(x_introspect_secret: str = Header(...,alias="X_Introspect_Secret"), authorization: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """
    Validate and introspect a token, returning its associated data if valid.
    
    The token should be provided in the Authorization header as 'Bearer <token>'.
    """
    
    if x_introspect_secret != X_INTROSPECT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized"
        )

    token = authorization.credentials

    try:
        # First check if token exists in Redis cache
        oauth_accessor = Oauth2AsAccessor()
        token_data = oauth_accessor.get_cached_oauth2_token(token, metadata=False)
        
        if (not isinstance(token_data, dict)) or (not token_data.get("active", False)) or time.time() > token_data.get("exp", 000):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Expired or invalid"
            )
        
        user_id = token_data["user_id"]
        tenant_id = token_data.get("tenant_id", "")
        
        # Get user's roles and permissions
        user = UserController().get_user(user_id, db)
        roles = crud.get_user_roles(db, user_id)
        permissions = crud.get_user_permissions(db, user_id)
        
        # Create full token payload
        current_time = int(time.time())
        expiry_time = token_data.get("exp", current_time + (TOKEN_EXPIRY_HOURS * 3600))
        
        token_payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "email": user.username,
            "roles": roles,
            "permissions": permissions,
            "token_type": "access",
            "iat": token_data.get("iat", current_time),
            "exp": expiry_time,
            "active": True,
            "jti": token_data.get("jti", secrets.token_hex(8)),
        }
            
        return token_payload
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Token validation failed: {str(e)}"
        )


@router.post("/revoke")
async def revoke_token(authorization: str = Header(...)):
    """
    Revoke a token so it can no longer be used for authentication.
    
    The token should be provided in the Authorization header as 'Bearer <token>'.
    """
    token_parts = authorization.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid authorization header format"
        )
    
    token = token_parts[1]
    oauth_accessor = Oauth2AsAccessor()
    
    if oauth_accessor.revoke_token(token):
        return {"message": "Token revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke token or token not found"
        )


@router.get("/me")
async def get_me(       
    user: dict = Depends(PermissionChecker(["user_management.read"]))
):
    return {"user": user}

@router.post("/login", response_model=TokenResponse)
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Get user's roles and permissions
    roles = crud.get_user_roles(db, user.user_id)
    permissions = crud.get_user_permissions(db, user.user_id)
    
    # Generate an opaque token to return to the client
    opaque_token = secrets.token_hex(16)
    
    # Create token payload with metadata
    current_time = int(time.time())
    expiry_time = current_time + (TOKEN_EXPIRY_HOURS * 3600)
    
    # Full metadata payload
    token_payload = {
        "user_id": user.user_id,
        "tenant_id": user.tenant_id,
        "email": form_data.username,
        "roles": roles,
        "permissions": permissions,
        "token_type": "access",
        "iat": current_time,
        "exp": expiry_time,
        "jti": secrets.token_hex(8),  # JWT ID for uniqueness
    }
    
    # Store the mapping between opaque token and JWT payload in Redis
    oauth_accessor = Oauth2AsAccessor()
    ttl = expiry_time - current_time
    
    if not oauth_accessor.store_opaque_token(opaque_token, token_payload, ttl):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store authentication token"
        )
    
    return TokenResponse(access_token=opaque_token, token_type="bearer", permissions=permissions)
