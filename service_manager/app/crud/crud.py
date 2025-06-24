from sqlalchemy.orm import Session
from app.database.models import Tenant, Service, Group, Policy, User, user_tenant, group_role, user_role, group_user
from app.api.schemas.schemas import *
from sqlalchemy import select, and_
from typing import List, Optional

# Tenant CRUD operations
def create_tenant(db: Session, tenant: TenantCreate):
    db_tenant = Tenant(name=tenant.name)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

def get_tenant(db: Session, tenant_id: int):
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()

def get_tenants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Tenant).offset(skip).limit(limit).all()

def update_tenant(db: Session, tenant_id: int, tenant_update: TenantCreate):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if db_tenant:
        db_tenant.name = tenant_update.name
        db.commit()
        db.refresh(db_tenant)
    return db_tenant

def patch_tenant(db: Session, tenant_id: int, tenant_update: dict):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if db_tenant:
        for key, value in tenant_update.items():
            if hasattr(db_tenant, key):
                setattr(db_tenant, key, value)
        db.commit()
        db.refresh(db_tenant)
    return db_tenant

def delete_tenant(db: Session, tenant_id: int):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if db_tenant:
        db.delete(db_tenant)
        db.commit()
    return db_tenant

# Service CRUD operations
def create_service(db: Session, service: ServiceCreate):
    db_service = Service(name=service.name, description=service.description)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def get_service(db: Session, service_id: int):
    return db.query(Service).filter(Service.id == service_id).first()

def get_services(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Service).offset(skip).limit(limit).all()

def update_service(db: Session, service_id: int, service_update: ServiceCreate):
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if db_service:
        db_service.name = service_update.name
        db_service.description = service_update.description
        db.commit()
        db.refresh(db_service)
    return db_service

def patch_service(db: Session, service_id: int, service_update: dict):
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if db_service:
        for key, value in service_update.items():
            if hasattr(db_service, key):
                setattr(db_service, key, value)
        db.commit()
        db.refresh(db_service)
    return db_service

def delete_service(db: Session, service_id: int):
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if db_service:
        db.delete(db_service)
        db.commit()
    return db_service

# Group CRUD operations
def create_group(db: Session, group: GroupCreate):
    db_group = Group(name=group.name, description=group.description, tenant_id=group.tenant_id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def get_group(db: Session, group_id: int):
    return db.query(Group).filter(Group.id == group_id).first()

def get_groups(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Group).offset(skip).limit(limit).all()

def update_group(db: Session, group_id: int, group_update: GroupCreate):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group:
        db_group.name = group_update.name
        db_group.tenant_id = group_update.tenant_id
        db.commit()
        db.refresh(db_group)
    return db_group

def patch_group(db: Session, group_id: int, group_update: dict):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group:
        for key, value in group_update.items():
            if hasattr(db_group, key):
                setattr(db_group, key, value)
        db.commit()
        db.refresh(db_group)
    return db_group

def delete_group(db: Session, group_id: int):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group:
        db.delete(db_group)
        db.commit()
    return db_group

# Policy CRUD operations
def get_policies(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tenant_id: int = None,
    service_id: int = None,
    group_id: int = None,
    role_id: int = None,
    user_id: int = None,
    action: str = None,
    resource: str = None,
):
    query = db.query(Policy)
    if tenant_id is not None:
        query = query.filter(Policy.tenant_id == tenant_id)
    if service_id is not None:
        query = query.filter(Policy.service_id == service_id)
    if group_id is not None:
        query = query.filter(Policy.group_id == group_id)
    if role_id is not None:
        query = query.filter(Policy.role_id == role_id)
    if user_id is not None:
        query = query.filter(Policy.user_id == user_id)
    if action is not None:
        query = query.filter(Policy.action == action)
    if resource is not None:
        query = query.filter(Policy.resource == resource)
    return query.offset(skip).limit(limit).all()

def get_policy(db: Session, policy_id: int):
    return db.query(Policy).filter(Policy.id == policy_id).first()

def update_policy(db: Session, policy_id: int, policy_update):
    db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if db_policy:
        db_policy.tenant_id = policy_update.tenant_id
        db_policy.service_id = policy_update.service_id
        db_policy.resource = policy_update.resource
        db_policy.action = policy_update.action
        db_policy.group_id = policy_update.group_id
        db_policy.role_id = policy_update.role_id
        db_policy.user_id = policy_update.user_id
        db_policy.condition = policy_update.condition
        db.commit()
        db.refresh(db_policy)
    return db_policy

def patch_policy(db: Session, policy_id: int, policy_update: dict):
    db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if db_policy:
        for key, value in policy_update.items():
            if hasattr(db_policy, key):
                setattr(db_policy, key, value)
        db.commit()
        db.refresh(db_policy)
    return db_policy

def delete_policy(db: Session, policy_id: int):
    db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if db_policy:
        db.delete(db_policy)
        db.commit()
    return db_policy

# User cruds
def create_user(db: Session, user: UserCreate):
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=user.hashed_password,
        full_name=user.full_name,
        is_active=user.is_active if hasattr(user, "is_active") else 1
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def verify_password(plain_password: str, hashed_password: str):
    # Replace with actual password hashing in production
    return plain_password == hashed_password

def update_user(db: Session, user_id: int, user_update: UserCreate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.username = user_update.username
        db_user.email = user_update.email
        db_user.hashed_password = user_update.hashed_password
        db_user.full_name = user_update.full_name
        db_user.is_active = user_update.is_active if hasattr(user_update, "is_active") else db_user.is_active
        db.commit()
        db.refresh(db_user)
    return db_user

def patch_user(db: Session, user_id: int, user_update: dict):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        for key, value in user_update.items():
            if hasattr(db_user, key):
                setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# User-Tenant mapping
def add_user_tenant(db: Session, user_id: int, tenant_id: int, metadata: dict = None):
    stmt = user_tenant.insert().values(user_id=user_id, tenant_id=tenant_id, metadata=metadata)
    db.execute(stmt)
    db.commit()
    return {"added": True}

def list_user_tenants(db: Session):
    stmt = select(user_tenant)
    return db.execute(stmt).fetchall()

def remove_user_tenant(db: Session, user_id: int, tenant_id: int):
    stmt = user_tenant.delete().where(
        and_(user_tenant.c.user_id == user_id, user_tenant.c.tenant_id == tenant_id)
    )
    db.execute(stmt)
    db.commit()
    return {"removed": True}

# Group-Role mapping
def add_group_role(db: Session, group_id: int, role_id: int):
    stmt = group_role.insert().values(group_id=group_id, role_id=role_id)
    db.execute(stmt)
    db.commit()
    return {"added": True}

def list_group_roles(db: Session):
    stmt = select(group_role)
    return db.execute(stmt).fetchall()

def remove_group_role(db: Session, group_id: int, role_id: int):
    stmt = group_role.delete().where(
        and_(group_role.c.group_id == group_id, group_role.c.role_id == role_id)
    )
    db.execute(stmt)
    db.commit()
    return {"removed": True}

# User-Role mapping
def add_user_role(db: Session, user_id: int, role_id: int, tenant_id: int):
    stmt = user_role.insert().values(user_id=user_id, role_id=role_id, tenant_id=tenant_id)
    db.execute(stmt)
    db.commit()
    return {"added": True}

def list_user_roles(db: Session):
    stmt = select(user_role)
    return db.execute(stmt).fetchall()

def remove_user_role(db: Session, user_id: int, role_id: int, tenant_id: int):
    stmt = user_role.delete().where(
        and_(
            user_role.c.user_id == user_id,
            user_role.c.role_id == role_id,
            user_role.c.tenant_id == tenant_id
        )
    )
    db.execute(stmt)
    db.commit()
    return {"removed": True}

# Group-User mapping
def add_group_user(db: Session, group_id: int, user_id: int):
    stmt = group_user.insert().values(group_id=group_id, user_id=user_id)
    db.execute(stmt)
    db.commit()
    return {"added": True}

def list_group_users(db: Session):
    stmt = select(group_user)
    return db.execute(stmt).fetchall()

def remove_group_user(db: Session, group_id: int, user_id: int):
    stmt = group_user.delete().where(
        and_(group_user.c.group_id == group_id, group_user.c.user_id == user_id)
    )
    db.execute(stmt)
    db.commit()
    return {"removed": True}