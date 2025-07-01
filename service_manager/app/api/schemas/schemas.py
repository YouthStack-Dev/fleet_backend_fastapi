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
        from_attributes = True

class CompanyCreate(BaseModel):
    name: str
    tenant_id: int

class CompanyRead(CompanyCreate):
    id: int
    class Config:
        from_attributes = True

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ServiceRead(ServiceCreate):
    id: int
    class Config:
        from_attributes = True

class GroupCreate(BaseModel):
    group_name: str
    tenant_id: int
    description: Optional[str] = None

class GroupRead(GroupCreate):
    group_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    # tenant_id: int
    department_name: str
    description: Optional[str]


class DepartmentCreate(DepartmentBase):
    pass

class DepartmentRead(DepartmentBase):
    department_id: int


class DepartmentUpdate(BaseModel):
    department_name: Optional[str]
    description: Optional[str]


class DepartmentOut(DepartmentBase):
    department_id: int

    class Config:
        from_attributes = True

class EmployeeCreate(BaseModel):
    user_id: int
    employee_name: str
    gender: Optional[str]
    mobile_number: Optional[str]
    alternate_mobile_number: Optional[str]
    office: Optional[str]
    special_need: Optional[str]
    subscribe_via_email: Optional[bool] = False
    subscribe_via_sms: Optional[bool] = False
    address: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    landmark: Optional[str]

class RoleCreate(BaseModel):
    role_name: str
    description: Optional[str] = None
    tenant_id: int

class RoleRead(RoleCreate):
    role_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ModuleCreate(BaseModel):
    service_id: int
    name: str
    description: Optional[str] = None

class ModuleRead(ModuleCreate):
    id: int

    class Config:
        from_attributes = True

class PolicyEndpointCreate(BaseModel):
    endpoint: str

class PolicyEndpointRead(PolicyEndpointCreate):
    id: int
    class Config:
        from_attributes = True

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
        from_attributes = True

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
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Constraints(BaseModel):
    ip_range: str


class PermissionItem(BaseModel):
    module: str
    service: str
    module_id: int
    service_id: int
    action: List[str]
    resource: str
    constraints: Constraints


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    permissions: List[PermissionItem] = []

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str