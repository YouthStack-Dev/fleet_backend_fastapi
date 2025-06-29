from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class TenantCreate(BaseModel):
    tenant_name: str
    tenant_metadata: Optional[Dict] = None
    is_active: Optional[int] = 1

class TenantRead(TenantCreate):
    tenant_id: int
    created_at: datetime
    updated_at: datetime

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
    group_name: str
    tenant_id: int
    description: Optional[str] = None

class GroupRead(GroupCreate):
    group_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RoleCreate(BaseModel):
    role_name: str
    description: Optional[str] = None
    tenant_id: int

class RoleRead(RoleCreate):
    role_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ModuleCreate(BaseModel):
    service_id: int
    name: str
    description: Optional[str] = None

class ModuleRead(ModuleCreate):
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
    tenant_id: int
    service_id: int
    module_id: Optional[int] = None
    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False
    group_id: Optional[int] = None
    role_id: Optional[int] = None
    user_id: Optional[int] = None
    condition: Optional[Dict] = None

class PolicyRead(PolicyCreate):
    policy_id: int

    class Config:
        orm_mode = True

class AssignPolicyRequest(BaseModel):
    group_id: int
    policy_id: int

class UserCreate(BaseModel):
    username: str
    email: str
    hashed_password: str
    tenant_id: int
    is_active: Optional[int] = 1

class UserRead(BaseModel):
    user_id: int
    username: str
    email: str
    tenant_id: int
    is_active: int
    created_at: datetime
    updated_at: datetime

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