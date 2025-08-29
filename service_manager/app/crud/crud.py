import math
import uuid
from fastapi.responses import JSONResponse
import pandas as pd 
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Driver, Tenant, Service, Group, Policy, User, Role, Module, user_tenant, group_role, user_role, group_user,Cutoff , Shift
from app.api.schemas.schemas import *
from sqlalchemy import select, and_, or_
from typing import List, Optional
from app.crud.errors import handle_integrity_error
from app.database.models import Department
from fastapi import File, HTTPException, UploadFile

from common_utils.auth.utils import hash_password


import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# Tenant CRUD operations
def create_tenant(db: Session, tenant: TenantCreate):
    try:
        logger.info(f"Create tenant request received: {tenant.dict()}")

        db_tenant = Tenant(
            tenant_name=tenant.tenant_name.strip(),
            tenant_metadata=tenant.tenant_metadata,
            is_active=tenant.is_active
        )

        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)

        logger.info(f"Tenant created successfully with tenant_id: {db_tenant.tenant_id}")
        return db_tenant
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError while creating tenant: {str(e)}")
        raise HTTPException(status_code=409, detail="Tenant already exists or unique constraint violated.")
    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while creating tenant: {str(e)}")
        raise HTTPException(status_code=500, detail="A database error occurred while creating the tenant.")

    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error while creating tenant: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the tenant.")

def get_tenant(db: Session, tenant_id: int):
    return db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()

def get_tenants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Tenant).offset(skip).limit(limit).all()

def update_tenant(db: Session, tenant_id: int, tenant_update: TenantCreate):
    try:
        logger.info(f"Update request received for tenant_id: {tenant_id}, payload: {tenant_update.dict()}")

        db_tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()

        if not db_tenant:
            logger.warning(f"Tenant with tenant_id {tenant_id} not found.")
            raise HTTPException(status_code=404, detail="Tenant not found.")

        # Update fields only if provided
        if tenant_update.tenant_name is not None:
            db_tenant.tenant_name = tenant_update.tenant_name.strip()

        if tenant_update.tenant_metadata is not None:
            db_tenant.tenant_metadata = tenant_update.tenant_metadata

        if tenant_update.is_active is not None:
            if tenant_update.is_active not in (0, 1):
                logger.warning(f"Invalid is_active value provided: {tenant_update.is_active}")
                raise HTTPException(status_code=422, detail="is_active must be either 0 (inactive) or 1 (active).")
            
            db_tenant.is_active = tenant_update.is_active

        db.commit()
        db.refresh(db_tenant)

        logger.info(f"Tenant with tenant_id {tenant_id} updated successfully.")
        return db_tenant
    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError while updating tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=409, detail="Tenant update violates unique constraint.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while updating tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="A database error occurred while updating the tenant.")

    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error while updating tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the tenant.")

def patch_tenant(db: Session, tenant_id: int, tenant_update: dict):
    try:
        db_tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if db_tenant:
            for key, value in tenant_update.items():
                if hasattr(db_tenant, key):
                    setattr(db_tenant, key, value)
            db.commit()
            db.refresh(db_tenant)
        return db_tenant
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def delete_tenant(db: Session, tenant_id: int):
    try:
        db_tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()  

        if not db_tenant:  
            logger.warning(f"Tenant with tenant_id {tenant_id} not found.")  
            raise HTTPException(status_code=404, detail="Tenant not found.")  

        db.delete(db_tenant)  
        db.commit()  

        logger.info(f"Tenant with tenant_id {tenant_id} deleted successfully.")  
        return {"message": f"Tenant {tenant_id} deleted successfully."}  

    except IntegrityError as e:  
        db.rollback()  
        logger.error(f"IntegrityError while deleting tenant {tenant_id}: {str(e)}")  
        raise HTTPException(status_code=409, detail="Cannot delete tenant due to related data constraints.")  

    except SQLAlchemyError as e:  
        db.rollback()  
        logger.error(f"Database error while deleting tenant {tenant_id}: {str(e)}")  
        raise HTTPException(status_code=500, detail="A database error occurred while deleting the tenant.")  
    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    except Exception as e:  
        db.rollback()  
        logger.exception(f"Unexpected error while deleting tenant {tenant_id}: {str(e)}")  
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting the tenant.")  

# Service CRUD operations
def create_service(db: Session, service: ServiceCreate):
    try:
        db_service = Service(
            name=service.name,
            description=service.description,
            service_metadata={}
        )
        db.add(db_service)
        db.commit()
        db.refresh(db_service)
        return db_service
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)
    
def seed_services(db: Session):
    try:
        default_services = [
            {"name": "User Management", "description": "Manage users, roles, and permissions"},
            {"name": "Shift Management", "description": "Manage employee shifts and logs"},
            {"name": "Booking Management", "description": "Manage bookings and assignments"},
            {"name": "Driver Management", "description": "Manage drivers and their documents"},
            {"name": "Vehicle Management", "description": "Manage vehicles and maintenance"},
        ]

        created_services = []
        for service_data in default_services:
            # check if exists
            existing = db.query(Service).filter(Service.name == service_data["name"]).first()
            if not existing:
                new_service = Service(
                    name=service_data["name"],
                    description=service_data["description"],
                    service_metadata={}
                )
                db.add(new_service)
                created_services.append(new_service)

        db.commit()
        for s in created_services:
            db.refresh(s)

        return created_services
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def get_service(db: Session, service_id: int):
    return db.query(Service).filter(Service.id == service_id).first()

def get_services(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Service).offset(skip).limit(limit).all()

def update_service(db: Session, service_id: int, service_update: ServiceCreate):
    try:
        db_service = db.query(Service).filter(Service.id == service_id).first()
        if db_service:
            db_service.name = service_update.name
            db_service.description = service_update.description
            db.commit()
            db.refresh(db_service)
        return db_service
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def patch_service(db: Session, service_id: int, service_update: dict):
    try:
        db_service = db.query(Service).filter(Service.id == service_id).first()
        if db_service:
            for key, value in service_update.items():
                if hasattr(db_service, key):
                    setattr(db_service, key, value)
            db.commit()
            db.refresh(db_service)
        return db_service
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def delete_service(db: Session, service_id: int):
    try:
        db_service = db.query(Service).filter(Service.id == service_id).first()
        if db_service:
            db.delete(db_service)
            db.commit()
        return db_service
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

# Group CRUD operations
def create_group(db: Session, group: GroupCreate):
    try:
        db_group = Group(
            group_name=group.group_name,
            tenant_id=group.tenant_id,
            description=group.description
        )
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        return db_group
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def get_group(db: Session, group_id: int):
    return db.query(Group).filter(Group.group_id == group_id).first()

def get_groups(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Group).offset(skip).limit(limit).all()

def update_group(db: Session, group_id: int, group_update: GroupCreate):
    try:
        db_group = db.query(Group).filter(Group.group_id == group_id).first()
        if db_group:
            db_group.group_name = group_update.group_name
            db_group.tenant_id = group_update.tenant_id
            db_group.description = group_update.description
            db.commit()
            db.refresh(db_group)
        return db_group
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def patch_group(db: Session, group_id: int, group_update: dict):
    try:
        db_group = db.query(Group).filter(Group.group_id == group_id).first()
        if db_group:
            for key, value in group_update.items():
                if hasattr(db_group, key):
                    setattr(db_group, key, value)
            db.commit()
            db.refresh(db_group)
        return db_group
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def delete_group(db: Session, group_id: int):
    try:
        db_group = db.query(Group).filter(Group.group_id == group_id).first()
        if db_group:
            db.delete(db_group)
            db.commit()
        return db_group
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

# Policy CRUD operations
def create_policy(db: Session, policy: PolicyCreate):
    try:
        db_policy = Policy(
            tenant_id=policy.tenant_id,
            service_id=policy.service_id,
            module_id=policy.module_id,
            can_view=policy.can_view,
            can_create=policy.can_create,
            can_edit=policy.can_edit,
            can_delete=policy.can_delete,
            group_id=policy.group_id,
            role_id=policy.role_id,
            user_id=policy.user_id,
            condition=policy.condition
        )
        db.add(db_policy)
        db.commit()
        db.refresh(db_policy)
        return db_policy
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

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
    return db.query(Policy).filter(Policy.policy_id == policy_id).first()

def update_policy(db: Session, policy_id: int, policy_update):
    try:
        db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if db_policy:
            db_policy.tenant_id = policy_update.tenant_id
            db_policy.service_id = policy_update.service_id
            db_policy.module_id = policy_update.module_id
            db_policy.can_view = policy_update.can_view
            db_policy.can_create = policy_update.can_create
            db_policy.can_edit = policy_update.can_edit
            db_policy.can_delete = policy_update.can_delete
            db_policy.group_id = policy_update.group_id
            db_policy.role_id = policy_update.role_id
            db_policy.user_id = policy_update.user_id
            db_policy.condition = policy_update.condition
            db.commit()
            db.refresh(db_policy)
        return db_policy
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def patch_policy(db: Session, policy_id: int, policy_update: dict):
    try:
        db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if db_policy:
            for key, value in policy_update.items():
                if hasattr(db_policy, key):
                    setattr(db_policy, key, value)
            db.commit()
            db.refresh(db_policy)
        return db_policy
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def delete_policy(db: Session, policy_id: int):
    try:
        db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if db_policy:
            db.delete(db_policy)
            db.commit()
        return db_policy
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

# User cruds
def create_user(db: Session, user: UserCreate):
    try:
        db_user = User(
            username=user.username,
            email=user.email,
            mobile_number=user.mobile_number,
            hashed_password=user.hashed_password,
            tenant_id=user.tenant_id,
            is_active=user.is_active if user.is_active is not None else 1
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()



def update_user(db: Session, user_id: int, user_update: UserCreate):
    try:
        db_user = db.query(User).filter(User.user_id == user_id).first()
        if db_user:
            for key, value in user_update.dict().items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
            return db_user
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def patch_user(db: Session, user_id: int, user_update: dict):
    try:
        db_user = db.query(User).filter(User.user_id == user_id).first()
        if db_user:
            for key, value in user_update.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def delete_user(db: Session, user_id: int):
    try:
        db_user = db.query(User).filter(User.user_id == user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
        return db_user
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

# User-Tenant mapping
def add_user_tenant(db: Session, user_id: int, tenant_id: int, metadata: dict = None):
    try:
        stmt = user_tenant.insert().values(
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata
        )
        db.execute(stmt)
        db.commit()
        return {"status": "success", "message": "User added to tenant"}
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def list_user_tenants(db: Session):
    stmt = select(user_tenant)
    return db.execute(stmt).fetchall()

def remove_user_tenant(db: Session, user_id: int, tenant_id: int):
    try:
        stmt = user_tenant.delete().where(
            and_(user_tenant.c.user_id == user_id, user_tenant.c.tenant_id == tenant_id)
        )
        db.execute(stmt)
        db.commit()
        return {"removed": True}
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

# Group-Role mapping
def add_group_role(db: Session, group_id: int, role_id: int):
    try:
        stmt = group_role.insert().values(group_id=group_id, role_id=role_id)
        db.execute(stmt)
        db.commit()
        return {"added": True}
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def list_group_roles(db: Session):
    stmt = select(group_role)
    return db.execute(stmt).fetchall()

def remove_group_role(db: Session, group_id: int, role_id: int):
    try:
        stmt = group_role.delete().where(
            and_(group_role.c.group_id == group_id, group_role.c.role_id == role_id)
        )
        db.execute(stmt)
        db.commit()
        return {"removed": True}
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

# User-Role mapping
def add_user_role(db: Session, user_id: int, role_id: int, tenant_id: int):
    try:
        stmt = user_role.insert().values(user_id=user_id, role_id=role_id, tenant_id=tenant_id)
        db.execute(stmt)
        db.commit()
        return {"added": True}
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def list_user_roles(db: Session):
    stmt = select(user_role)
    return db.execute(stmt).fetchall()

def remove_user_role(db: Session, user_id: int, role_id: int, tenant_id: int):
    try:
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
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

# Group-User mapping
def add_group_user(db: Session, group_id: int, user_id: int):
    try:
        stmt = group_user.insert().values(
            group_id=group_id,
            user_id=user_id
        )
        db.execute(stmt)
        db.commit()
        return {"status": "success", "message": "User added to group"}
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

def list_group_users(db: Session):
    stmt = select(group_user)
    return db.execute(stmt).fetchall()

def remove_group_user(db: Session, group_id: int, user_id: int):
    try:
        stmt = group_user.delete().where(
            and_(group_user.c.group_id == group_id, group_user.c.user_id == user_id)
        )
        db.execute(stmt)
        db.commit()
        return {"removed": True}
    except Exception as e:
        db.rollback()
        raise handle_integrity_error(e)

# User roles and permissions
def get_user_roles(db: Session, user_id: int):
    stmt = select(Role.role_name).join(user_role).join(User).where(User.user_id == user_id)
    return [row[0] for row in db.execute(stmt).fetchall()]

def get_user_permissions(db: Session, user_id: int):
    query = (
        select(
            Service.name.label('service_name'),
            Module.name.label('module_name'),
            Policy.service_id,
            Policy.module_id,
            Policy.can_view,
            Policy.can_create,
            Policy.can_edit,
            Policy.can_delete,
            Policy.condition
        )
        .join(Service, Policy.service_id == Service.id)
        .join(Module, Policy.module_id == Module.id)
        .join(Group, Policy.group_id == Group.group_id, isouter=True)
        .join(group_user, Group.group_id == group_user.c.group_id, isouter=True)
        .join(Role, Policy.role_id == Role.role_id, isouter=True)
        .join(user_role, Role.role_id == user_role.c.role_id, isouter=True)
        .where(
            or_(
                Policy.user_id == user_id,
                group_user.c.user_id == user_id,
                user_role.c.user_id == user_id
            )
        )
    )
    
    permissions = []
    for row in db.execute(query).fetchall():
        actions = []
        if row.can_view:
            actions.append("read")
        if row.can_create:
            actions.append("create")
        if row.can_edit:
            actions.append("update")
        if row.can_delete:
            actions.append("delete")
            
        permissions.append({
            "module": row.module_name,
            "service": row.service_name,
            "module_id": row.module_id,
            "service_id": row.service_id,
            "action": actions,
            "resource": row.service_name,
            "constraints": row.condition or {}
        })
    
    return permissions




# Department CRUD operations

def create_department(db, department_data, tenant_id):
    try:
        department = Department(
            tenant_id=tenant_id,
            department_name=department_data.department_name,
            description=department_data.description
        )
        db.add(department)
        db.commit()
        db.refresh(department)
        return department

    except IntegrityError as e:
        db.rollback()
        if 'uix_department_tenant' in str(e.orig):
            raise HTTPException(status_code=409, detail="Department with this name already exists for the tenant.")
        raise HTTPException(status_code=400, detail="Database integrity error.")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error occurred.")
    
def get_departments(db, tenant_id: int, skip: int = 0, limit: int = 100):
    try:
        logger.info(f"Fetching departments for tenant {tenant_id} with skip={skip} and limit={limit}")

        departments = db.query(Department).filter_by(tenant_id=tenant_id).offset(skip).limit(limit).all()

        if not departments:
            logger.warning(f"No departments found for tenant {tenant_id}")
            return []

        department_list = []
        for department in departments:
            # Total employees in department
            employee_count = db.query(Employee).filter(
                Employee.department_id == department.department_id,
                Employee.tenant_id == tenant_id
            ).count()

            # Active employees in department
            active_count = db.query(Employee).filter(
                Employee.department_id == department.department_id,
                Employee.tenant_id == tenant_id,
                Employee.is_active == True
            ).count()

            # Inactive employees in department
            inactive_count = db.query(Employee).filter(
                Employee.department_id == department.department_id,
                Employee.tenant_id == tenant_id,
                Employee.is_active == False
            ).count()

            department_list.append({
                "department_id": department.department_id,
                "department_name": department.department_name,
                "description": department.description,
                "employee_count": employee_count,
                "active_count": active_count,
                "inactive_count": inactive_count,
            })

        logger.info(f"Found {len(department_list)} departments for tenant {tenant_id}")
        return department_list

    except Exception as e:
        logger.exception(f"Unexpected error while fetching departments for tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching departments.")

# def get_departments(db, tenant_id, skip=0, limit=100):
#     try:
#         return db.query(Department).filter_by(tenant_id=tenant_id).offset(skip).limit(limit).all()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching departments.")


def update_department(db, department_id, department, tenant_id):
    try:
        db_department = db.query(Department).filter_by(department_id=department_id, tenant_id=tenant_id).first()
        if not db_department:
            raise HTTPException(status_code=404, detail="Department not found.")

        db_department.department_name = department.department_name
        db_department.description = department.description

        db.commit()
        db.refresh(db_department)
        return db_department

    except IntegrityError as e:
        db.rollback()
        if 'uix_department_tenant' in str(e.orig):
            raise HTTPException(status_code=409, detail="Department with this name already exists for the tenant.")
        raise HTTPException(status_code=400, detail="Database integrity error during update.")
    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error occurred while updating department.")


def delete_department(db, department_id, tenant_id):
    try:
        logger.info(f"Delete request received for department_id: {department_id} under tenant_id: {tenant_id}")
        db_department = db.query(Department).filter_by(department_id=department_id, tenant_id=tenant_id).first()  

        if not db_department:  
            logger.warning(f"Department with department_id {department_id} not found for tenant {tenant_id}")  
            raise HTTPException(status_code=404, detail="Department not found for this tenant.")  

        db.delete(db_department)  
        db.commit()  

        logger.info(f"Department {department_id} successfully deleted for tenant {tenant_id}")  
        return {"message": f"Department {department_id} deleted successfully."}  

    except IntegrityError as e:  
        db.rollback()  
        logger.error(f"IntegrityError while deleting department {department_id} for tenant {tenant_id}: {str(e)}")  
        raise HTTPException(status_code=409, detail="Cannot delete department due to related data constraints.")  
    
    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    
    except SQLAlchemyError as e:  
        db.rollback()  
        logger.error(f"Database error while deleting department {department_id} for tenant {tenant_id}: {str(e)}")  
        raise HTTPException(status_code=500, detail="A database error occurred while deleting the department.")  

    except Exception as e:  
        db.rollback()  
        logger.exception(f"Unexpected error while deleting department {department_id} for tenant {tenant_id}: {str(e)}")  
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting the department.")  

    



from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.database.models import Employee, User, Tenant, Department
from app.firebase.employee_push import push_employee_to_firebase



def create_employee(db: Session, employee, tenant_id):
    try:
        logger.info(f"Creating employee for tenant_id: {tenant_id}, payload: {employee.dict()}")

        # --------- Required field validations ---------
        if not employee.name or not employee.name.strip():
            logger.warning("Missing name in payload")
            raise HTTPException(status_code=422, detail="Name is required.")

        if not employee.employee_code or not employee.employee_code.strip():
            logger.warning("Missing employee_code in payload")
            raise HTTPException(status_code=422, detail="Employee code is required.")

        if not employee.email or not employee.email.strip():
            logger.warning("Missing email in payload")
            raise HTTPException(status_code=422, detail="Email is required.")

        if not employee.mobile_number or not employee.mobile_number.strip():
            logger.warning("Missing mobile_number in payload")
            raise HTTPException(status_code=422, detail="Mobile number is required.")

        # --------- Validate special_need logic ---------
        allowed_special_needs = ['pregnancy', 'others', 'none', None]
        special_need = employee.special_need.lower() if employee.special_need else None

        if special_need not in allowed_special_needs:
            logger.warning(f"Invalid special_need value: {employee.special_need}")
            raise HTTPException(status_code=422, detail="Invalid special_need. Allowed values are: pregnancy, others, none.")

        if special_need == 'none':
            special_need = None

        if special_need:
            if not employee.special_need_start_date or not employee.special_need_end_date:
                logger.warning("special_need is provided but start/end dates are missing.")
                raise HTTPException(status_code=422, detail="special_need_start_date and special_need_end_date are required.")

            if employee.special_need_start_date > employee.special_need_end_date:
                logger.warning("special_need_start_date is after special_need_end_date.")
                raise HTTPException(status_code=422, detail="special_need_start_date must be before special_need_end_date.")
        else:
            employee.special_need_start_date = None
            employee.special_need_end_date = None

        # --------- Uniqueness checks ---------
        existing_emp_code = db.query(Employee).filter_by(employee_code=employee.employee_code).first()
        if existing_emp_code:
            logger.warning(f"Employee code {employee.employee_code} already exists.")
            raise HTTPException(status_code=409, detail="Employee code already exists.")

        existing_mobile = db.query(Employee).filter_by(mobile_number=employee.mobile_number.strip(), tenant_id=tenant_id).first()
        if existing_mobile:
            logger.warning(f"Mobile number {employee.mobile_number} already exists.")
            raise HTTPException(status_code=409, detail="Mobile number already exists.")

        existing_email = db.query(Employee).filter_by(email=employee.email.strip(), tenant_id=tenant_id).first()
        if existing_email:
            logger.warning(f"Email {employee.email} already exists.")
            raise HTTPException(status_code=409, detail="Email already exists.")
        

        # --------- Validate tenant and department ---------
        tenant = db.query(Tenant).filter_by(tenant_id=tenant_id).first()
        if not tenant:
            logger.error(f"Tenant not found with tenant_id: {tenant_id}")
            raise HTTPException(status_code=404, detail="Tenant not found.")

        department = db.query(Department).filter_by(department_id=employee.department_id, tenant_id=tenant_id).first()
        if not department:
            logger.error(f"Department {employee.department_id} not found for tenant {tenant_id}")
            raise HTTPException(status_code=404, detail="Department not found for this tenant.")

        # --------- Validate coordinates ---------
        try:
            if employee.latitude:
                float(employee.latitude)
            if employee.longitude:
                float(employee.longitude)
        except ValueError:
            logger.warning("Invalid latitude or longitude provided.")
            raise HTTPException(status_code=422, detail="Latitude and Longitude must be valid coordinates.")

        # --------- Create employee ---------
        db_employee = Employee(
            employee_code=employee.employee_code.strip(),
            name=employee.name.strip(),
            email=employee.email.strip(),
            mobile_number=employee.mobile_number.strip(),
            hashed_password=hash_password(employee.employee_code.strip()),
            department_id=employee.department_id,
            tenant_id=tenant_id,
            gender=employee.gender,
            alternate_mobile_number=employee.alternate_mobile_number,
            office=employee.office,
            special_need=special_need,
            special_need_start_date=employee.special_need_start_date,
            special_need_end_date=employee.special_need_end_date,
            subscribe_via_email=employee.subscribe_via_email if employee.subscribe_via_email is not None else False,
            subscribe_via_sms=employee.subscribe_via_sms if employee.subscribe_via_sms is not None else False,
            address=employee.address,
            latitude=employee.latitude,
            longitude=employee.longitude,
            landmark=employee.landmark
        )

        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        

        # Push to Firebase after DB commit
        try:
            push_employee_to_firebase(
                tenant_id=tenant_id,
                department_id=employee.department_id,
                employee_code=db_employee.employee_code,
                employee_id=db_employee.employee_id,
                name=db_employee.name
            )
        except Exception as e:
            logger.error(f"Failed to push employee to Firebase: {str(e)}")

        logger.info(f"Employee created successfully with ID: {db_employee.employee_code}")
        return {
            "employee_code": db_employee.employee_code,
            "employee_id": db_employee.employee_id,
            "name": db_employee.name,
            "email": db_employee.email,
            "mobile_number": db_employee.mobile_number,
            "department_id": db_employee.department_id,
            "gender": db_employee.gender,
            "alternate_mobile_number": db_employee.alternate_mobile_number,
            "office": db_employee.office,
            "special_need": db_employee.special_need,
            "special_need_start_date": db_employee.special_need_start_date,
            "special_need_end_date": db_employee.special_need_end_date,
            "subscribe_via_email": db_employee.subscribe_via_email,
            "subscribe_via_sms": db_employee.subscribe_via_sms,
            "address": db_employee.address,
            "latitude": db_employee.latitude,
            "longitude": db_employee.longitude,
            "landmark": db_employee.landmark,
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {str(e.orig)}")
        raise HTTPException(status_code=400, detail="Database integrity error while creating employee.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating employee.")

    except HTTPException as e:
        db.rollback()
        logger.warning(f"HTTPException: {str(e.detail)}")
        raise e

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error while creating employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while creating employee.")

    

def clean_for_json(val):
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val

def clean_employee_dict(emp_dict):
    """Recursively clean dict values for JSON serialization."""
    for k, v in emp_dict.items():
        if isinstance(v, dict):
            emp_dict[k] = clean_employee_dict(v)
        else:
            emp_dict[k] = clean_for_json(v)
    return emp_dict

def safe_float(val):
    """Convert pandas float to JSON-safe float or None."""
    if val is None or pd.isna(val) or isinstance(val, float) and math.isnan(val):
        return None
    return float(val)

ALLOWED_SPECIAL_NEEDS = ['pregnancy', 'others', 'none', None]


def bulk_create_employees(file, tenant_id: int, db: Session):

    logger.info(f"Starting bulk employee creation for tenant_id: {tenant_id}, file: {file.filename}")

    if not file.filename.endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file format: {file.filename}")
        raise HTTPException(status_code=400, detail="Only Excel files are allowed.")

    try:
        df = pd.read_excel(file.file)
        logger.info(f"Excel file read successfully with {len(df)} rows")

        required_columns = ['name', 'email', 'mobile_number', 'department_id', 'employee_code']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing required columns: {missing_cols}")
            raise HTTPException(status_code=422, detail=f"Missing required columns in Excel: {missing_cols}")

        created_employees = []
        skipped_employees = []
        errors = []
        employees_to_add = []

        tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            logger.error(f"Tenant not found: {tenant_id}")
            raise HTTPException(status_code=404, detail="Tenant not found.")
        logger.info(f"Tenant found: {tenant.tenant_name}")

        for idx, row in df.iterrows():
            logger.info(f"Processing row {idx + 2}: {row.to_dict()}")
            try:
                mobile_val_str = None
                if pd.notna(row.get('mobile_number')):
                    try:
                        mobile_val_str = str(int(float(row.get('mobile_number'))))
                    except (ValueError, TypeError):
                        row_issues.append("Invalid mobile_number")
                latitude = safe_float(row.get('latitude'))
                longitude = safe_float(row.get('longitude'))
                alternate_mobile_val = safe_float(row.get('alternate_mobile_number'))
                row_issues = []

                # --- Required fields ---
                name_val = row.get('name')
                email_val = row.get('email')
                mobile_val = row.get('mobile_number')
                department_id_val = row.get('department_id')
                employee_code_val = row.get('employee_code')

                if pd.isna(name_val) or not str(name_val).strip():
                    row_issues.append("Missing name")
                if pd.isna(email_val) or not str(email_val).strip():
                    row_issues.append("Missing email")
                mobile_val = row.get('mobile_number')
                mobile_val_str = None
                if pd.isna(mobile_val):
                    row_issues.append("Missing mobile_number")
                else:
                    try:
                        # Convert to integer safely
                        mobile_val_str = str(int(float(mobile_val)))
                    except (ValueError, TypeError):
                        row_issues.append("Invalid mobile_number")
                if pd.isna(department_id_val):
                    row_issues.append("Missing department_id")
                if pd.isna(employee_code_val) or not str(employee_code_val).strip():
                    row_issues.append("Missing employee_code")

                # Normalize for DB checks
                email_val = str(email_val).strip() if pd.notna(email_val) else None
                mobile_val = mobile_val_str
                employee_code_val = str(employee_code_val).strip() if pd.notna(employee_code_val) else None
                department_id_int = int(department_id_val) if pd.notna(department_id_val) else None

                # --- Duplicate checks ---
                if email_val and db.query(Employee).filter(Employee.email == email_val, Employee.tenant_id == tenant_id).first():
                    row_issues.append(f"Email {email_val} exists")
                if mobile_val and db.query(Employee).filter(Employee.mobile_number == mobile_val, Employee.tenant_id == tenant_id).first():
                    row_issues.append(f"Mobile {mobile_val} exists")
                if employee_code_val and db.query(Employee).filter(Employee.employee_code == employee_code_val, Employee.tenant_id == tenant_id).first():
                    row_issues.append(f"Employee code {employee_code_val} exists")

                # --- Special need checks ---
                special_need_val = str(row.get('special_need')).lower() if row.get('special_need') else None
                if special_need_val and special_need_val not in ALLOWED_SPECIAL_NEEDS:
                    row_issues.append(f"Invalid special_need: {special_need_val}")
                if special_need_val and special_need_val != 'none':
                    special_need_start_date = row.get('special_need_start_date')
                    if pd.isna(special_need_start_date):
                        special_need_start_date = None

                    special_need_end_date = row.get('special_need_end_date')
                    if pd.isna(special_need_end_date):
                        special_need_end_date = None

                    if special_need_val and special_need_val != 'none':
                        if not special_need_start_date or not special_need_end_date:
                            row_issues.append("Missing special_need_start_date or special_need_end_date")
                        elif special_need_start_date > special_need_end_date:
                            row_issues.append("special_need_start_date > special_need_end_date")


                # --- Department check ---
                department = db.query(Department).filter(
                    Department.department_id == department_id_int,
                    Department.tenant_id == tenant_id
                ).first()
                if not department:
                    row_issues.append(f"Department {department_id_val} not found")

                # --- Coordinates check ---
                latitude_val = row.get('latitude')
                if pd.notna(latitude_val) and not math.isnan(latitude_val):
                    latitude_val = float(latitude_val)
                else:
                    latitude_val = None

                longitude_val = row.get('longitude')
                if pd.notna(longitude_val) and not math.isnan(longitude_val):
                    longitude_val = float(longitude_val)
                else:
                    longitude_val = None
                # --- Skip row if any issues ---
                if row_issues:
                    skipped_employees.append({
                        "row": idx + 2,
                        "issues": row_issues,
                        "department_id": department_id_val,
                        "reason": "Row validation failed"
                    })
                    continue

                # --- Prepare final values ---
                name = str(name_val).strip()
                email = email_val
                mobile_number = mobile_val
                gender = row.get('gender')
                office = row.get('office')
                alternate_mobile_number = row.get('alternate_mobile_number')
                subscribe_via_email = bool(row.get('subscribe_via_email', False))
                subscribe_via_sms = bool(row.get('subscribe_via_sms', False))
                address = row.get('address')
                landmark = row.get('landmark')
                special_need = None if special_need_val == 'none' else special_need_val
                special_need_start_date = row.get('special_need_start_date') if special_need else None
                special_need_end_date = row.get('special_need_end_date') if special_need else None

                db_employee = Employee(
                    employee_code=employee_code_val,
                    name=name,
                    email=email,
                    mobile_number=mobile_number,
                    hashed_password=hash_password(employee_code_val),
                    department_id=department.department_id,
                    tenant_id=tenant_id,
                    gender=gender,
                    alternate_mobile_number=alternate_mobile_number,
                    office=office,
                    special_need=special_need,
                    special_need_start_date=special_need_start_date,
                    special_need_end_date=special_need_end_date,
                    subscribe_via_email=subscribe_via_email,
                    subscribe_via_sms=subscribe_via_sms,
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                    landmark=landmark
                )
                employees_to_add.append(db_employee)
                logger.info(f"Prepared employee object for {employee_code_val} at row {idx + 2}")

            except Exception as row_error:
                logger.error(f"Error processing row {idx + 2}: {row_error}")
                errors.append({"row": idx + 2, "error": str(row_error)})

        # --- Insert all valid employees ---
        try:
            db.add_all(employees_to_add)
            db.commit()
            logger.info(f"Inserted {len(employees_to_add)} employees into the database")
            for emp in employees_to_add:
                department = db.query(Department).filter(Department.department_id == emp.department_id).first()
                created_employees.append({
                    "employee_code": emp.employee_code,
                    "employee_id": emp.employee_id,
                    "name": emp.name,
                    "email": emp.email,
                    "mobile_number": emp.mobile_number,
                    "department_id": emp.department_id,
                    "department_name": department.department_name if department else None,
                    "gender": emp.gender,
                    "alternate_mobile_number": emp.alternate_mobile_number,
                    "office": emp.office,
                    "special_need": emp.special_need,
                    "special_need_start_date": emp.special_need_start_date,
                    "special_need_end_date": emp.special_need_end_date,
                    "subscribe_via_email": emp.subscribe_via_email,
                    "subscribe_via_sms": emp.subscribe_via_sms,
                    "address": emp.address,
                    "latitude": emp.latitude,
                    "longitude": emp.longitude,
                    "landmark": emp.landmark
                })

                try:
                    push_employee_to_firebase(
                        tenant_id=tenant_id,
                        department_id=emp.department_id,
                        employee_code=emp.employee_code,
                        employee_id=emp.employee_id,
                        name=emp.name
                    )
                    logger.info(f"Pushed employee {emp.employee_code} to Firebase")
                except Exception as e:
                    logger.error(f"Firebase push failed for {emp.employee_code}: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Bulk insert failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save employees to the database.")

        logger.info(f"Bulk employee creation completed. Created: {len(created_employees)}, Skipped: {len(skipped_employees)}, Errors: {len(errors)}")
        created_employees = [clean_employee_dict(emp) for emp in created_employees]
        skipped_employees = [clean_employee_dict(emp) for emp in skipped_employees]
        errors = [clean_employee_dict(emp) for emp in errors]

        return {
            "created": created_employees,
            "skipped": skipped_employees,
            "errors": errors
        }
    except Exception as e:
        logger.error(f"Bulk employee creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process the Excel file.")

import traceback

def get_employee(db: Session, employee_code, tenant_id):
    try:
        logger.info(f"Fetching employee with employee_code: {employee_code} under tenant_id: {tenant_id}")
        
        employees = (
            db.query(Employee)
            .join(Employee.department)  # Ensure the department is joined
            .filter(Employee.employee_code == employee_code)
            .filter(Employee.tenant_id == tenant_id)
            .first()
        )

        if not employees:
            logger.warning(f"Employee {employee_code} not found for tenant {tenant_id}")
            raise HTTPException(status_code=404, detail="Employee not found.")

        logger.info(f"Employee fetched: {employees.employee_code}, user: {employees.name}, email: {employees.email}")

        employee_data = {
            "employee_code": employees.employee_code,
            "gender": employees.gender,
            "mobile_number": employees.mobile_number,
            "alternate_mobile_number": employees.alternate_mobile_number,
            "office": employees.office,
            "special_need": employees.special_need,
            "special_need_start_date": employees.special_need_start_date,
            "special_need_end_date": employees.special_need_end_date,
            "subscribe_via_email": employees.subscribe_via_email,
            "subscribe_via_sms": employees.subscribe_via_sms,
            "address": employees.address,
            "latitude": employees.latitude,
            "longitude": employees.longitude,
            "landmark": employees.landmark,
            "department_id": employees.department_id,
            "department_name": employees.department.department_name,  # ✅ added
            "employee_id": employees.employee_id,
            "name": employees.name,
            "email": employees.email
        }

        logger.info(f"Returning employee data: {employee_data}")
        return employee_data

    except HTTPException as e:
        logger.warning(f"HTTPException while fetching employee: {str(e.detail)}")
        raise e
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Exception while fetching employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during query execution")

def get_employee_by_department(db: Session, department_id: int, tenant_id: int,
                               is_active: Optional[bool], page: int, page_size: int):
    try:
        logger.info(f"Fetching employees for department_id={department_id}, tenant_id={tenant_id}, "
                    f"is_active={is_active}, page={page}, page_size={page_size}")

        # Validate department
        department = db.query(Department).filter_by(
            department_id=department_id,
            tenant_id=tenant_id
        ).first()
        if not department:
            logger.warning(f"Department {department_id} not found for tenant {tenant_id}")
            raise HTTPException(status_code=404, detail="Department not found.")

        # Base query
        query = db.query(Employee).filter(
            Employee.department_id == department_id,
            Employee.tenant_id == tenant_id
        )

        # Apply is_active filter if provided
        if is_active is not None:
            query = query.filter(Employee.is_active == is_active)

        # Count before pagination
        total_count = query.count()

        # Apply pagination
        employees = (
            query.order_by(Employee.employee_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        if not employees:
            logger.warning(f"No employees found for department {department_id}, tenant {tenant_id}, "
                           f"is_active={is_active}")
            raise HTTPException(status_code=404, detail="No employees found for this department.")

        # Build response list
        employee_list = [
            {
                "employee_id": emp.employee_id,
                "employee_code": emp.employee_code,
                "name": emp.name,
                "email": emp.email,
                "gender": emp.gender,
                "mobile_number": emp.mobile_number,
                "alternate_mobile_number": emp.alternate_mobile_number,
                "office": emp.office,
                "special_need": emp.special_need,
                "special_need_start_date": emp.special_need_start_date,
                "special_need_end_date": emp.special_need_end_date,
                "subscribe_via_email": emp.subscribe_via_email,
                "subscribe_via_sms": emp.subscribe_via_sms,
                "address": emp.address,
                "latitude": emp.latitude,
                "longitude": emp.longitude,
                "landmark": emp.landmark,
                "department_name": department.department_name,
                "department_id": department_id,
                "is_active": emp.is_active
            }
            for emp in employees
        ]

        return {
            "department_id": department_id,
            "department_name": department.department_name,
            "tenant_id": tenant_id,
            "total_employees": total_count,
            "page": page,
            "page_size": page_size,
            "employees": employee_list
        }

    except HTTPException as e:
        raise e  # Let FastAPI handle 404s
    except Exception as e:
        logger.exception("Unhandled exception in get_employee_by_department")
        raise HTTPException(status_code=500, detail="Internal server error")

def get_employee_by_tenant(
    db: Session, tenant_id: int, page: int = 1, limit: int = 50
) -> EmployeesByTenantResponse:
    try:
        logger.info(f"Fetching employees for tenant_id={tenant_id}, page={page}, limit={limit}")

        # Fetch all employees for the tenant with pagination
        query = db.query(Employee).filter(Employee.tenant_id == tenant_id)
        total_employees = query.count()

        # Apply pagination
        employees = query.offset((page - 1) * limit).limit(limit).all()

        if not employees:
            logger.warning(f"No employees found for tenant_id={tenant_id}")
            raise HTTPException(status_code=404, detail="No employees found for this tenant.")

        employee_list: List[EmployeeResponse] = []
        for emp in employees:
            employee_list.append(EmployeeResponse(
                employee_code=emp.employee_code,
                employee_id=emp.employee_id,
                name=emp.name,
                email=emp.email,
                gender=emp.gender,
                mobile_number=emp.mobile_number,
                alternate_mobile_number=emp.alternate_mobile_number,
                office=emp.office,
                special_need=emp.special_need,
                special_need_start_date=emp.special_need_start_date,
                special_need_end_date=emp.special_need_end_date,
                subscribe_via_email=emp.subscribe_via_email,
                subscribe_via_sms=emp.subscribe_via_sms,
                address=emp.address,
                latitude=emp.latitude,
                longitude=emp.longitude,
                landmark=emp.landmark,
                department_name=emp.department.department_name if emp.department else None,
                department_id=emp.department_id
            ))

        return EmployeesByTenantResponse(
            tenant_id=tenant_id,
            total_employees=total_employees,
            employees=employee_list
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Unhandled exception in get_employees_by_tenant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

def update_employee(db: Session, employee_code: str, employee_update: EmployeeUpdate, tenant_id: int):
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Update request for employee_code={employee_code}, tenant_id={tenant_id}, payload={employee_update.dict(exclude_unset=True)}")

    try:
        # 1️⃣ Fetch Employee
        db_employee = db.query(Employee).filter(
            Employee.employee_code == employee_code,
            Employee.tenant_id == tenant_id
        ).first()

        logger.info(f"Found employee: {db_employee}")

        if not db_employee:
            return JSONResponse(
                    status_code=404,
                    content={
                        "status": "error",
                        "code": 404,
                        "message": "Employee not found for this tenant.",
                        "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
                        "data": None
                    }
                )

        # 2️⃣ Check duplicate employee_code (if updated)
        if employee_update.employee_code and employee_update.employee_code != db_employee.employee_code:
            existing_code = db.query(Employee).filter(
                Employee.employee_code == employee_update.employee_code,
                Employee.tenant_id == tenant_id,
                Employee.employee_id != db_employee.employee_id
            ).first()
            if existing_code:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "code": 400,
                        "message": "Employee code already exists for this tenant.",
                        "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
                        "data": None
                    }
                )

        # 3️⃣ Check duplicate email (if updated)
        if employee_update.email and employee_update.email.strip().lower() != (db_employee.email or "").lower():
            new_email = employee_update.email.strip().lower()
            existing_email = db.query(Employee).filter(
                Employee.email == new_email,
                Employee.tenant_id == tenant_id,
                Employee.employee_id != db_employee.employee_id
            ).first()
            if existing_email:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "code": 400,
                        "message": "Email already exists for another employee in this tenant.",
                        "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
                        "data": None
                    }
                )
            # ✅ Update email if no duplicate found
            db_employee.email = new_email
        # 4️⃣ Check duplicate mobile number (if updated)
        if employee_update.mobile_number and employee_update.mobile_number != db_employee.mobile_number:
            existing_mobile = db.query(Employee).filter(
                Employee.mobile_number == employee_update.mobile_number,
                Employee.tenant_id == tenant_id,
                Employee.employee_id != db_employee.employee_id
            ).first()
            if existing_mobile:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "code": 400,
                        "message": "Mobile number already exists for another employee in this tenant.",
                        "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
                        "data": None
                    }
                )

        # 2️⃣ Validate Department
        if employee_update.department_id is not None:
            department = db.query(Department).filter_by(
                department_id=employee_update.department_id,
                tenant_id=tenant_id
            ).first()
            if not department:
                logger.error(f"[{request_id}] Invalid department_id={employee_update.department_id}")
                raise HTTPException(status_code=404, detail="Department not found for this tenant.")
            db_employee.department_id = employee_update.department_id


        # --------- Validate Latitude & Longitude if provided ---------
        try:
            if employee_update.latitude is not None:
                float(employee_update.latitude)
            if employee_update.longitude is not None:
                float(employee_update.longitude)
        except ValueError:
            logger.warning("Invalid latitude or longitude provided.")
            raise HTTPException(status_code=422, detail="Latitude and Longitude must be valid coordinates.")
        # 4️⃣ Special Need Logic
        special_need = employee_update.special_need.lower() if employee_update.special_need else None
        start_date = employee_update.special_need_start_date
        end_date = employee_update.special_need_end_date

        allowed_special_needs = ["pregnancy", "others", "none"]

       # ✅ Case 1: special_need provided
        if special_need:
            if special_need not in allowed_special_needs:
                logger.warning(f"[{request_id}] Invalid special_need={special_need}")
                return EmployeeUpdateResponse(
                    status="error",
                    code=422,
                    message=f"Invalid special_need. Allowed: {', '.join(allowed_special_needs)}",
                    meta=Meta(
                        request_id=request_id,
                        timestamp=datetime.utcnow().isoformat()
                    ),
                    data=None
                )

            # ❌ 'none' should not have any dates
            if special_need == "none":
                if start_date or end_date:
                    logger.warning(f"[{request_id}] Dates provided with special_need=none")
                    return EmployeeUpdateResponse(
                        status="error",
                        code=422,
                        message="Do not provide dates when special_need is 'none'.",
                        meta=Meta(
                            request_id=request_id,
                            timestamp=datetime.utcnow().isoformat()
                        ),
                        data=None
                    )
                db_employee.special_need = None
                db_employee.special_need_start_date = None
                db_employee.special_need_end_date = None

            else:
                # ✅ Must provide both dates
                if not start_date or not end_date:
                    logger.warning(f"[{request_id}] Missing dates for special_need={special_need}")
                    return EmployeeUpdateResponse(
                        status="error",
                        code=422,
                        message="Start and end dates are required when special_need is provided.",
                        meta=Meta(
                            request_id=request_id,
                            timestamp=datetime.utcnow().isoformat()
                        ),
                        data=None
                    )
                # ✅ Compare dates safely
                if start_date and end_date and start_date > end_date:
                    logger.warning(f"[{request_id}] Invalid date range for special_need={special_need}")
                    return EmployeeUpdateResponse(
                        status="error",
                        code=422,
                        message="special_need_start_date must be before special_need_end_date.",
                        meta=Meta(
                            request_id=request_id,
                            timestamp=datetime.utcnow().isoformat()
                        ),
                        data=None
                    )

                db_employee.special_need = special_need
                db_employee.special_need_start_date = start_date
                db_employee.special_need_end_date = end_date

        # ✅ Case 2: No special_need, but dates provided → Error
        elif start_date or end_date:
            logger.warning(f"[{request_id}] Dates provided without special_need")
            return EmployeeUpdateResponse(
                status="error",
                code=422,
                message="Cannot provide special_need dates without specifying a special_need.",
                meta=Meta(
                    request_id=request_id,
                    timestamp=datetime.utcnow().isoformat()
                ),
                data=None
            )


        # 5️⃣ Generic Field Updates (only provided ones)
        updatable_fields = [
            "employee_code", "gender", "name", "mobile_number", "alternate_mobile_number",
            "office", "subscribe_via_email", "subscribe_via_sms", "address",
            "latitude", "longitude", "landmark"
        ]
        for field in updatable_fields:
            value = getattr(employee_update, field)
            if value is not None:
                setattr(db_employee, field, value.strip() if isinstance(value, str) else value)

        # 6️⃣ Commit changes
        db.commit()
        db.refresh(db_employee)
        logger.info(f"[{request_id}] Employee updated successfully")

        # 7️⃣ Push to Firebase (non-blocking failure)
        try:
            from app.firebase.employee_push import push_employee_to_firebase
            push_employee_to_firebase(
                tenant_id=tenant_id,
                department_id=db_employee.department_id,
                employee_code=db_employee.employee_code,
                employee_id=db_employee.employee_id,
                name=db_employee.name
            )
        except Exception as e:
            logger.error(f"[{request_id}] Firebase sync failed: {str(e)}")

        # 8️⃣ Structured Response
        return {
            "status": "success",
            "code": 200,
            "message": f"Employee {db_employee.employee_code} updated successfully",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {
                "employee_code": db_employee.employee_code,
                "employee_id": db_employee.employee_id,
                "name": db_employee.name,
                "email": db_employee.email,
                "gender": db_employee.gender,
                "mobile_number": db_employee.mobile_number,
                "alternate_mobile_number": db_employee.alternate_mobile_number,
                "office": db_employee.office,
                "department_id": db_employee.department_id,
                "department_name": db_employee.department.department_name if db_employee.department else None,
                "special_need": db_employee.special_need,
                "special_need_start_date": db_employee.special_need_start_date,
                "special_need_end_date": db_employee.special_need_end_date,
                "subscribe_via_email": db_employee.subscribe_via_email,
                "subscribe_via_sms": db_employee.subscribe_via_sms,
                "address": db_employee.address,
                "latitude": db_employee.latitude,
                "longitude": db_employee.longitude,
                "landmark": db_employee.landmark,
            }
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"[{request_id}] IntegrityError: {str(e.orig)}")
        return {
            "status": "error",
            "code": 400,
            "message": "Database integrity error while updating employee.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[{request_id}] SQLAlchemyError: {str(e)}")
        return {
            "status": "error",
            "code": 500,
            "message": "Database error while updating employee.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }

    except HTTPException as e:
        db.rollback()
        logger.warning(f"[{request_id}] HTTPException while updating employee: {str(e.detail)}")
        return {
            "status": "error",
            "code": e.status_code,
            "message": str(e.detail),
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }

    except Exception as e:
        db.rollback()
        logger.error(f"[{request_id}] Unexpected error: {str(e)}")
        return {
            "status": "error",
            "code": 500,
            "message": "Unexpected error while updating employee.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    
def update_employee_status(self, employee_code: str, is_active: bool, db: Session, tenant_id: int):
    try:
        employee = db.query(Employee).filter_by(
            employee_code=employee_code,
            tenant_id=tenant_id
        ).first()

        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        employee.is_active = is_active
        db.commit()
        db.refresh(employee)

        logger.info(f"Employee {employee_code} status updated to {is_active} by tenant {tenant_id}")
        return EmployeeUpdateStatusResponse(
            employee_code=employee.employee_code,
            is_active=employee.is_active
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update employee status {employee_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update employee status")


def delete_employee(db: Session, employee_code: str, tenant_id: int):
    try:
        logger.info(f"Delete request received for employee_code: {employee_code} in tenant_id: {tenant_id}")

        # Fetch employee with tenant check
        db_employee = db.query(Employee).filter(
            Employee.employee_code == employee_code,
            Employee.tenant_id == tenant_id
        ).first()

        if not db_employee:
            logger.warning(f"Employee {employee_code} not found for tenant {tenant_id}")
            raise HTTPException(status_code=404, detail="Employee not found for this tenant.")

        # Delete employee
        db.delete(db_employee)
        db.commit()

        logger.info(f"Employee {employee_code} successfully deleted for tenant {tenant_id}")
        return {"message": f"Employee {employee_code} deleted successfully."}

    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while deleting employee {employee_code} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while deleting the employee.")

    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error while deleting employee {employee_code} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    

# app/crud/cutoff.py

def create_cutoff(db: Session, cutoff: CutoffCreate, tenant_id: int):
    existing = db.query(Cutoff).filter_by(tenant_id=tenant_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cutoff already exists for this tenant.")

    db_cutoff = Cutoff(
        tenant_id=tenant_id,
        booking_cutoff=cutoff.booking_cutoff,
        cancellation_cutoff=cutoff.cancellation_cutoff
    )
    db.add(db_cutoff)
    db.commit()
    db.refresh(db_cutoff)
    return db_cutoff


def get_cutoff_by_tenant(db: Session, tenant_id: int):
    return db.query(Cutoff).filter_by(tenant_id=tenant_id).first()

def update_cutoff(db: Session, tenant_id: int, cutoff_update: CutoffUpdate):
    cutoff = get_cutoff_by_tenant(db, tenant_id)
    if not cutoff:
        raise HTTPException(status_code=404, detail="Cutoff not found")

    for field, value in cutoff_update.dict().items():
        setattr(cutoff, field, value)

    db.commit()
    db.refresh(cutoff)
    return cutoff

def create_shift(db: Session, tenant_id: int, shift_data: ShiftCreate):
    existing = db.query(Shift).filter_by(tenant_id=tenant_id, shift_code=shift_data.shift_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Shift code already exists for this tenant.")

    # Convert list of days to comma-separated string
    db_shift = Shift(
        tenant_id=tenant_id,
        shift_code=shift_data.shift_code,
        log_type=shift_data.log_type,
        shift_time=shift_data.shift_time,
        day=",".join(shift_data.day),  # <-- Important!
        waiting_time_minutes=shift_data.waiting_time_minutes,
        pickup_type=shift_data.pickup_type,
        gender=shift_data.gender,
        is_active=shift_data.is_active
    )

    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift


def get_shifts(db: Session, tenant_id: int, skip: int = 0, limit: int = 100) -> List[Shift]:
    try:
        return (
            db.query(Shift)
            .filter(Shift.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch shifts")
    
def get_shift_by_id(db: Session, tenant_id: int, shift_id: int) -> Shift:
    try:
        shift = (
            db.query(Shift)
            .filter(Shift.tenant_id == tenant_id, Shift.id == shift_id)
            .first()
        )
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        return shift
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch shift")
    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    
def update_shift(db: Session, tenant_id: int, shift_id: int, shift_update: ShiftUpdate):
    shift = db.query(Shift).filter_by(id=shift_id, tenant_id=tenant_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    try:
        for key, value in shift_update.dict(exclude_unset=True).items():
            setattr(shift, key, value)

        db.commit()
        db.refresh(shift)
        return shift
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update shift")
    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    
def get_shifts_by_log_type(
    db: Session,
    tenant_id: int,
    log_type: LogType,
    skip: int = 0,
    limit: int = 100
):
    try:
        base_query = db.query(Shift).filter(
            Shift.tenant_id == tenant_id,
            Shift.log_type == log_type
        )


        shifts = base_query.offset(skip).limit(limit).all()

        return shifts
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch shifts by log type")
    except HTTPException as e:
    # Allow FastAPI to handle HTTP errors directly
        raise e
    
def delete_shift(db: Session, tenant_id: int, shift_id: int):
    shift = db.query(Shift).filter_by(id=shift_id, tenant_id=tenant_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    try:
        db.delete(shift)  # 👈 Hard delete
        db.commit()
        return {"detail": f"Shift ID {shift_id} deleted successfully."}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete shift")


from app.database.models import Vendor,Department

def create_vendor(db: Session, vendor_data, tenant_id: int):
    logger.info(f"Creating vendor: {vendor_data.vendor_name} for tenant_id: {tenant_id}")
    
    existing = db.query(Vendor).filter_by(vendor_name=vendor_data.vendor_name, tenant_id=tenant_id).first()
    if existing:
        logger.warning(f"Vendor '{vendor_data.vendor_name}' already exists for tenant_id: {tenant_id}")
        raise HTTPException(status_code=400, detail="Vendor with this name already exists.")

    new_vendor = Vendor(
        tenant_id=tenant_id,
        vendor_name=vendor_data.vendor_name,
        contact_person=vendor_data.contact_person,
        phone_number=vendor_data.phone_number,
        email=vendor_data.email,
        address=vendor_data.address,
    )
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)

    logger.info(f"Vendor created successfully: {new_vendor.vendor_id}")
    return new_vendor


def get_vendors(db: Session, tenant_id: int, skip: int, limit: int, is_active: Optional[bool]) -> List[Vendor]:
    try:
        logger.info(f"[SERVICE] Fetching vendors for tenant_id={tenant_id}, is_active={is_active}")
        query = db.query(Vendor).filter(Vendor.tenant_id == tenant_id)

        if is_active is not None:
            query = query.filter(Vendor.is_active == is_active)

        vendors = (
            query.order_by(Vendor.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.info(f"[SERVICE] Found {len(vendors)} vendors")
        return vendors
    except Exception as ex:
        logger.exception("[SERVICE] Error querying vendors from DB")
        raise


def get_vendor_by_id(db: Session, tenant_id: int, vendor_id: int) -> Vendor:
    logger.info(f"Fetching vendor_id: {vendor_id} for tenant_id: {tenant_id}")
    
    vendor = (
        db.query(Vendor)
        .filter(Vendor.tenant_id == tenant_id, Vendor.vendor_id == vendor_id)
        .first()
    )

    if not vendor:
        logger.error(f"Vendor with ID {vendor_id} not found for tenant_id: {tenant_id}")
        raise HTTPException(status_code=404, detail="Vendor not found")

    logger.info(f"Vendor found: {vendor.vendor_id}")
    return vendor


def update_vendor(db: Session, tenant_id: int, vendor_id: int, update_data):
    logger.info(f"Updating vendor_id: {vendor_id} for tenant_id: {tenant_id}")
    
    vendor = (
        db.query(Vendor)
        .filter(Vendor.vendor_id == vendor_id, Vendor.tenant_id == tenant_id)
        .first()
    )

    if not vendor:
        logger.error(f"Vendor with ID {vendor_id} not found for tenant_id: {tenant_id}")
        raise HTTPException(status_code=404, detail="Vendor not found")

    updates = update_data.dict(exclude_unset=True)
    logger.info(f"Fields to update: {updates}")
    
    for key, value in updates.items():
        setattr(vendor, key, value)

    db.commit()
    db.refresh(vendor)

    logger.info(f"Vendor updated successfully: {vendor.vendor_id}")
    return vendor
def delete_vendor(db: Session, tenant_id: int, vendor_id: int, user_id: int):
    vendor = (
        db.query(Vendor)
        .filter(Vendor.vendor_id == vendor_id, Vendor.tenant_id == tenant_id)
        .first()
    )

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    db.delete(vendor)
    db.commit()
    logger.info(f"Vendor {vendor_id} deleted successfully for tenant {tenant_id} by user {user_id}")
    return {"message": "Vendor deleted successfully"}

from app.database.models import VehicleType
from app.api.schemas.schemas import VehicleTypeCreate
def create_vehicle_type(db: Session, payload: VehicleTypeCreate):
    try:
        db_vehicle_type = VehicleType(**payload.dict())
        db.add(db_vehicle_type)
        db.commit()
        db.refresh(db_vehicle_type)

        logger.info(f"VehicleType created: {db_vehicle_type.name} (Vendor: {db_vehicle_type.vendor_id})")
        return db_vehicle_type

    except Exception as e:
        db.rollback()
        logger.exception("Error creating vehicle type")
        raise HTTPException(status_code=500, detail="Failed to create vehicle type")
    

def get_vehicle_type_by_id(db: Session, vehicle_type_id: int):
    try:
        vehicle_type = db.query(VehicleType).filter_by(vehicle_type_id=vehicle_type_id).first()
        if not vehicle_type:
            raise HTTPException(status_code=404, detail="Vehicle type not found")
        return vehicle_type
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching vehicle type with id={vehicle_type_id}")
        raise HTTPException(status_code=500, detail="Failed to fetch vehicle type")

def get_vehicle_types_filtered(
    db: Session,
    tenant_id: int,
    vendor_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    try:
        query = db.query(VehicleType).filter(VehicleType.vendor.has(tenant_id=tenant_id))

        if vendor_id:
            query = query.filter(VehicleType.vendor_id == vendor_id)

        return query.offset(skip).limit(limit).all()

    except Exception as e:
        logger.exception("Failed to fetch vehicle types (filtered)")
        raise HTTPException(status_code=500, detail="Unable to fetch vehicle types")

# app/crud/vehicle_type_crud.py

def update_vehicle_type(db: Session, vehicle_type_id: int, payload: VehicleTypeUpdate):
    try:
        vehicle_type = db.query(VehicleType).filter_by(vehicle_type_id=vehicle_type_id).first()
        if not vehicle_type:
            raise HTTPException(status_code=404, detail="Vehicle type not found")

        for key, value in payload.dict(exclude_unset=True).items():
            setattr(vehicle_type, key, value)

        db.commit()
        db.refresh(vehicle_type)

        logger.info(f"VehicleType updated: {vehicle_type_id}")
        return vehicle_type

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating vehicle type id={vehicle_type_id}")
        raise HTTPException(status_code=500, detail="Failed to update vehicle type")

# app/crud/vehicle_type_crud.py

def delete_vehicle_type(db: Session, vehicle_type_id: int):
    try:
        vehicle_type = db.query(VehicleType).filter_by(vehicle_type_id=vehicle_type_id).first()
        if not vehicle_type:
            raise HTTPException(status_code=404, detail="Vehicle type not found")

        db.delete(vehicle_type)
        db.commit()

        logger.info(f"VehicleType deleted: id={vehicle_type_id}")
        return {"message": "Vehicle type deleted successfully", "vehicle_type_id": vehicle_type_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error deleting vehicle type id={vehicle_type_id}")
        raise HTTPException(status_code=500, detail="Failed to delete vehicle type")
    
# from fastapi import HTTPException
# from sqlalchemy.exc import IntegrityError, SQLAlchemyError
# from uuid import uuid4
# import logging
# import os, shutil
# from fastapi import UploadFile
# logger = logging.getLogger(__name__)

# def create_driver(db: Session, driver, vendor_id: int):
#     try:
#         logger.info(f"Creating driver for vendor_id={vendor_id}, payload={driver.dict()}")

#         # --------- Required field validations ---------
#         if not driver.username or not driver.username.strip():
#             raise HTTPException(status_code=422, detail="Username is required.")
#         if not driver.email or not driver.email.strip():
#             raise HTTPException(status_code=422, detail="Email is required.")
#         if not driver.mobile_number or not driver.mobile_number.strip():
#             raise HTTPException(status_code=422, detail="Mobile number is required.")
#         if not driver.hashed_password:
#             raise HTTPException(status_code=422, detail="Password is required.")

#         # --------- Check Vendor ---------
#         vendor = db.query(Vendor).filter_by(vendor_id=vendor_id).first()
#         if not vendor:
#             logger.error(f"Vendor {vendor_id} not found.")
#             raise HTTPException(status_code=404, detail="Vendor not found.")

#         tenant_id = vendor.tenant_id

#         # --------- Uniqueness Checks ---------
#         existing_mobile_user = (
#             db.query(User)
#             .filter_by(mobile_number=driver.mobile_number.strip(), tenant_id=tenant_id)
#             .first()
#         )
#         if existing_mobile_user:
#             logger.warning(f"Mobile number {driver.mobile_number} already exists for tenant {tenant_id}")
#             raise HTTPException(status_code=409, detail="Mobile number already exists.")
        
#         # if driver.license_expiry_date and driver.license_expiry_date < date.today():
#         #     raise HTTPException(status_code=400, detail="License expiry date must be in the future.")

#         # --------- Check or create user ---------
#         db_user = db.query(User).filter_by(email=driver.email.strip(), tenant_id=tenant_id).first()
#         if db_user:
#             logger.info(f"User with email {driver.email} already exists with user_id={db_user.user_id}")

#             # Ensure the user is not already a driver
#             existing_driver = db.query(Driver).filter_by(user_id=db_user.user_id).first()
#             if existing_driver:
#                 raise HTTPException(status_code=409, detail="User is already registered as a driver.")
#             user_id = db_user.user_id
#         else:
#             logger.info(f"Creating new user: {driver.username}")
#             new_user = User(
#                 username=driver.username.strip(),
#                 email=driver.email.strip(),
#                 mobile_number=driver.mobile_number.strip(),
#                 hashed_password=driver.hashed_password,
#                 tenant_id=tenant_id,
#                 is_active=True,
#             )
#             db.add(new_user)
#             db.commit()
#             db.refresh(new_user)
#             user_id = new_user.user_id
#         # --------- UUID Generation ---------
#         driver_uuid = uuid4()

#         # --------- Document Saving ---------
#         def save_file(file: Optional[UploadFile], folder_name: str) -> Optional[str]:
#             if file:
#                 folder_path = os.path.join("uploaded_files", folder_name)
#                 os.makedirs(folder_path, exist_ok=True)
#                 file_path = os.path.join(folder_path, file.filename)
#                 with open(file_path, "wb") as f:
#                     shutil.copyfileobj(file.file, f)
#                 return file_path
#             return None

#         # --------- Create Driver ---------
#         new_driver = Driver(
#             user_id=user_id,
#             vendor_id=vendor_id,
#             # license_number=driver.license_number,
#             # license_expiry_date=driver.license_expiry_date,
#             uuid=driver_uuid,
#             city=driver.city,
#             date_of_birth=driver.date_of_birth,
#             gender=driver.gender,
#             alternate_mobile_number=driver.alternate_mobile_number,
#             permanent_address=driver.permanent_address,
#             current_address=driver.current_address,
#             bgv_status=driver.bgv_status,
#             bgv_date=driver.bgv_date,
#             bgv_doc_url=bgv_doc_url,
#             # police_doc_url=driver.police_doc_url,
#             # license_doc_url=driver.license_doc_url,
#             # photo_url=driver.photo_url,
#             is_active=True,
#         )

#         db.add(new_driver)
#         db.commit()
#         db.refresh(new_driver)


#         logger.info(f"Driver created successfully with driver_id: {new_driver.driver_id}")
#         return DriverOut(
#             driver_id=new_driver.driver_id,
#             uuid=new_driver.uuid,
#             user_id=new_driver.user_id,
#             username=new_driver.user.username,
#             email=new_driver.user.email,
#             mobile_number=new_driver.user.mobile_number,
#             vendor_id=new_driver.vendor_id,
#             city=new_driver.city,
#             date_of_birth=new_driver.date_of_birth,
#             gender=new_driver.gender,
#             alternate_mobile_number=new_driver.alternate_mobile_number,
#             permanent_address=new_driver.permanent_address,
#             current_address=new_driver.current_address,
#             bgv_status=new_driver.bgv_status,
#             bgv_date=new_driver.bgv_date,
#             # police_doc_url=new_driver.police_doc_url,
#             # license_doc_url=new_driver.license_doc_url,
#             # photo_url=new_driver.photo_url,
#             # is_active=new_driver.is_active,
#             # license_number=new_driver.license_number,
#             # license_expiry_date=new_driver.license_expiry_date,
#             created_at=new_driver.created_at,
#             updated_at=new_driver.updated_at,
#         )


#     except IntegrityError as e:
#         db.rollback()
#         logger.error(f"IntegrityError: {str(e.orig)}")
#         raise HTTPException(status_code=400, detail="Database integrity error while creating driver.")
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"SQLAlchemyError: {str(e)}")
#         raise HTTPException(status_code=500, detail="Database error while creating driver.")
#     except HTTPException as e:
#         db.rollback()
#         logger.warning(f"HTTPException: {str(e.detail)}")
#         raise e
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Unexpected error while creating driver: {str(e)}")
#         raise HTTPException(status_code=500, detail="Unexpected error while creating driver.")
