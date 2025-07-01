from pydantic import BaseModel
from typing import List, Optional

class TenantCreate(BaseModel):
    name: str

class TenantRead(TenantCreate):
    id: int
    class Config:
        orm_mode = True

class CompanyCreate(BaseModel):
    name: str
    tenant_id: int

class CompanyRead(CompanyCreate):
    id: int
    class Config:
        orm_mode = True

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ServiceRead(ServiceCreate):
    id: int
    class Config:
        orm_mode = True

class GroupCreate(BaseModel):
    name: str
    tenant_id: int

class GroupRead(GroupCreate):
    id: int
    class Config:
        orm_mode = True

class PolicyEndpointCreate(BaseModel):
    endpoint: str

class PolicyEndpointRead(PolicyEndpointCreate):
    id: int
    class Config:
        orm_mode = True

class PolicyCreate(BaseModel):
    name: str
    service_id: int
    endpoints: List[PolicyEndpointCreate] = []

class PolicyRead(BaseModel):
    id: int
    tenant_id: int
    service_id: int
    resource: Optional[str] = None
    action: str
    group_id: Optional[int] = None
    role_id: Optional[int] = None
    user_id: Optional[int] = None
    condition: Optional[dict] = None

    class Config:
        orm_mode = True

class AssignPolicyRequest(BaseModel):
    group_id: int
    policy_id: int

class UserCreate(BaseModel):
    username: str
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    is_active: Optional[int] = 1

class UserRead(UserCreate):
    id: int
    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str