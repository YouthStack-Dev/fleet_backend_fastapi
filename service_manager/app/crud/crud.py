from psycopg2 import IntegrityError
from sqlalchemy.orm import Session
from app.database.models import Driver, Tenant, Service, Group, Policy, User, Role, Module, user_tenant, group_role, user_role, group_user,Cutoff , Shift
from app.api.schemas.schemas import *
from sqlalchemy import select, and_, or_
from typing import List, Optional
from app.crud.errors import handle_integrity_error
from app.database.models import Department
from fastapi import HTTPException

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
            employee_count = db.query(Employee).join(User).filter(
                Employee.department_id == department.department_id,
                User.tenant_id == tenant_id
            ).count()

            department_list.append({
                "department_id": department.department_id,
                "department_name": department.department_name,
                "description": department.description,
                "employee_count": employee_count
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




def create_employee(db: Session, employee, tenant_id):
    try:
        logger.info(f"Creating employee for tenant_id: {tenant_id}, payload: {employee.dict()}")

        # --------- Required field validations ---------
        if not employee.username or not employee.username.strip():
            logger.warning("Missing username in payload")
            raise HTTPException(status_code=422, detail="Username is required.")

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

        # Normalize 'none' to None
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

        existing_mobile_user = (
            db.query(User)
            .filter_by(mobile_number=employee.mobile_number.strip(), tenant_id=tenant_id)
            .first()
        )
        if existing_mobile_user:
            logger.warning(f"Mobile number {employee.mobile_number} already exists.")
            raise HTTPException(status_code=409, detail="Mobile number already exists.")

        # --------- Check or create user ---------
        db_user = db.query(User).filter_by(email=employee.email.strip(), tenant_id=tenant_id).first()
        if db_user:
            logger.info(f"User with email {employee.email} already exists, user_id: {db_user.user_id}")
            existing_employee = db.query(Employee).filter_by(user_id=db_user.user_id).first()
            if existing_employee:
                logger.warning(f"User {db_user.user_id} is already an employee.")
                raise HTTPException(status_code=409, detail=f"User with email {db_user.email} is already an employee.")
            user_id = db_user.user_id
        else:

            logger.info(f"Creating new user: {employee.username}, email: {employee.email}")
            new_user = User(
                username=employee.username.strip(),
                email=employee.email.strip(),
                mobile_number=employee.mobile_number.strip(),
                hashed_password=employee.hashed_password,
                tenant_id=tenant_id,
                is_active=True
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_id = new_user.user_id

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
            user_id=user_id,
            department_id=employee.department_id,
            gender=employee.gender,
            alternate_mobile_number=employee.alternate_mobile_number,
            office=employee.office,
            special_need=employee.special_need,
            special_need_start_date=employee.special_need_start_date,
            special_need_end_date=employee.special_need_end_date,
            subscribe_via_email=employee.subscribe_via_email,
            subscribe_via_sms=employee.subscribe_via_sms,
            address=employee.address,
            latitude=employee.latitude,
            longitude=employee.longitude,
            landmark=employee.landmark
        )

        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)

        logger.info(f"Employee created successfully with ID: {db_employee.employee_code}")
        return {
            "employee_code": db_employee.employee_code,
            "department_id": db_employee.department_id,
            "user_id": db_employee.user_id,
            "username": db_employee.user.username,
            "email": db_employee.user.email,
            "gender": db_employee.gender,
            "mobile_number": db_employee.user.mobile_number,
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

import traceback

def get_employee(db: Session, employee_code, tenant_id):
    try:
        logger.info(f"Fetching employee with employee_code: {employee_code} under tenant_id: {tenant_id}")
        
        employees = (
            db.query(Employee)
            .join(Employee.user)
            .filter(Employee.employee_code == employee_code)
            .filter(User.tenant_id == tenant_id)
            .first()
        )

        if not employees:
            logger.warning(f"Employee {employee_code} not found for tenant {tenant_id}")
            raise HTTPException(status_code=404, detail="Employee not found.")

        logger.info(f"Employee fetched: {employees.employee_code}, user: {employees.user.username}, email: {employees.user.email}")
        # return employees
        return {
            "employee_code": employees.employee_code,
            "gender": employees.gender,
            "mobile_number": employees.user.mobile_number,
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
            "user_id": employees.user.user_id,
            "username": employees.user.username,
            "email": employees.user.email
        }
    except HTTPException as e:
        # Allow FastAPI to handle HTTP errors directly
        logger.warning(f"HTTPException while fetching employee: {str(e.detail)}")
        raise e
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Exception while fetching employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during query execution")

def get_employee_by_department(db: Session, department_id: int, tenant_id: int):
    logger.info(f"Fetching employees for department_id: {department_id} under tenant_id: {tenant_id}")

    employees = db.query(Employee).join(User).filter(
        Employee.department_id == department_id,
        User.tenant_id == tenant_id
    ).all()

    if not employees:
        logger.warning(f"No employees found for department {department_id} and tenant {tenant_id}")
        raise HTTPException(status_code=404, detail="No employees found for this department.")

    logger.info(f"Found {len(employees)} employees for department {department_id} under tenant {tenant_id}")

    employee_list = []
    for emp in employees:
        employee_list.append({
            "user_id": emp.user.user_id,
            "employee_code": emp.employee_code,
            "username": emp.user.username,
            "email": emp.user.email,
            "gender": emp.gender,
            "mobile_number": emp.user.mobile_number,
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

    return {
        "department_id": department_id,
        "tenant_id": tenant_id,
        "total_employees": len(employee_list),
        "employees": employee_list
    }


def update_employee(db: Session, employee_code: str, employee_update, tenant_id: int):
    try:
        logger.info(f"Updating employee with code: {employee_code} for tenant_id: {tenant_id}, payload: {employee_update.dict()}")

        db_employee = db.query(Employee).join(User).filter(
            Employee.employee_code == employee_code,
            User.tenant_id == tenant_id
        ).first()

        if not db_employee:
            logger.warning(f"Employee with code {employee_code} not found for tenant {tenant_id}")
            raise HTTPException(status_code=404, detail="Employee not found for this tenant.")

        # --------- Validate Department if provided ---------
        if employee_update.department_id is not None:
            department = db.query(Department).filter_by(department_id=employee_update.department_id, tenant_id=tenant_id).first()
            if not department:
                logger.error(f"Department {employee_update.department_id} not found for tenant {tenant_id}")
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

        # --------- Validate & Handle special_need logic ---------
        if employee_update.special_need is not None:
            special_need = employee_update.special_need.lower()
            allowed_special_needs = ['pregnancy', 'others', 'none']
            if special_need not in allowed_special_needs:
                logger.warning(f"Invalid special_need: {employee_update.special_need}")
                raise HTTPException(status_code=422, detail="Invalid special_need. Allowed: pregnancy, others, none.")

            # Normalize "none" to None
            if special_need == 'none':
                db_employee.special_need = None
                db_employee.special_need_start_date = None
                db_employee.special_need_end_date = None

                if employee_update.special_need_start_date or employee_update.special_need_end_date:
                    logger.warning("Dates provided for special_need = 'none'")
                    raise HTTPException(status_code=422, detail="Do not provide dates when special_need is 'none'.")
            else:
                # Dates must be provided
                if not employee_update.special_need_start_date or not employee_update.special_need_end_date:
                    logger.warning("special_need requires both start and end dates.")
                    raise HTTPException(status_code=422, detail="Start and end dates required for special_need.")

                if employee_update.special_need_start_date > employee_update.special_need_end_date:
                    logger.warning("special_need_start_date is after end_date.")
                    raise HTTPException(status_code=422, detail="special_need_start_date must be before end date.")

                db_employee.special_need = special_need
                db_employee.special_need_start_date = employee_update.special_need_start_date
                db_employee.special_need_end_date = employee_update.special_need_end_date

        # --------- Update other fields if provided ---------
        if employee_update.gender is not None:
            db_employee.gender = employee_update.gender

        if employee_update.mobile_number is not None:
            db_employee.mobile_number = employee_update.mobile_number.strip()

        if employee_update.alternate_mobile_number is not None:
            db_employee.alternate_mobile_number = employee_update.alternate_mobile_number

        if employee_update.office is not None:
            db_employee.office = employee_update.office

        if employee_update.subscribe_via_email is not None:
            db_employee.subscribe_via_email = employee_update.subscribe_via_email

        if employee_update.subscribe_via_sms is not None:
            db_employee.subscribe_via_sms = employee_update.subscribe_via_sms

        if employee_update.address is not None:
            db_employee.address = employee_update.address

        if employee_update.latitude is not None:
            db_employee.latitude = employee_update.latitude

        if employee_update.longitude is not None:
            db_employee.longitude = employee_update.longitude

        if employee_update.landmark is not None:
            db_employee.landmark = employee_update.landmark

        db.commit()
        db.refresh(db_employee)

        logger.info(f"Employee {employee_code} updated successfully for tenant {tenant_id}")
        return {
            "employee_code": db_employee.employee_code,
            "department_id": db_employee.department_id,
            "user_id": db_employee.user_id,
            "username": db_employee.user.username,
            "email": db_employee.user.email,
            "gender": db_employee.gender,
            "mobile_number": db_employee.user.mobile_number,
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
        logger.error(f"IntegrityError while updating employee: {str(e.orig)}")
        raise HTTPException(status_code=400, detail="Database integrity error while updating employee.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError while updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating employee.")

    except HTTPException as e:
        db.rollback()
        logger.warning(f"HTTPException while updating employee: {str(e.detail)}")
        raise e

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error while updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while updating employee.")

def delete_employee(db: Session, employee_code: str, tenant_id: int):
    try:
        logger.info(f"Delete request received for employee_code: {employee_code} in tenant_id: {tenant_id}")

        # Fetch employee with tenant check
        db_employee = db.query(Employee).join(User).filter(
            Employee.employee_code == employee_code,
            User.tenant_id == tenant_id
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

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

from app.database.models import Vendor

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

def create_driver(db: Session, driver: DriverCreate, vendor_id: int):
    try:
        logger.info(f"Creating driver for vendor_id={vendor_id} with payload={driver.dict()}")

        if not driver.username.strip():
            raise HTTPException(status_code=422, detail="Username is required.")
        if not driver.email.strip():
            raise HTTPException(status_code=422, detail="Email is required.")
        if not driver.hashed_password.strip():
            raise HTTPException(status_code=422, detail="Password is required.")

        # Step 1: Validate vendor existence
        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")

        tenant_id = vendor.tenant_id  # Extract tenant_id from vendor

        # Step 2: Check if user exists by email or phone
        db_user = db.query(User).filter(
            or_(
                User.email == driver.email
            )
        ).first()

        if db_user:
            logger.info(f"User already exists: user_id={db_user.user_id}, email={db_user.email}")
            existing_driver = db.query(Driver).filter_by(user_id=db_user.user_id).first()
            if existing_driver:
                raise HTTPException(status_code=409, detail="User already registered as a driver.")
            user_id = db_user.user_id
        else:
            # Step 3: Create new user
            logger.info(f"Creating new user for driver: {driver.email}")
            new_user = User(
                username=driver.username,
                email=driver.email,
                hashed_password=driver.hashed_password,
                tenant_id=tenant_id,
                is_active=1
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_id = new_user.user_id
            logger.info(f"New user created with user_id={user_id}")

        # Step 4: Create the Driver
        new_driver = Driver(
            user_id=user_id,
            vendor_id=vendor_id,
            city=driver.city,
            date_of_birth=driver.date_of_birth,
            gender=driver.gender,
            alternate_mobile_number=driver.alternate_mobile_number,
            permanent_address=driver.permanent_address,
            current_address=driver.current_address,
            bgv_status=driver.bgv_status or "Pending",
            bgv_date=driver.bgv_date,
            police_doc_url=driver.police_doc_url,
            license_doc_url=driver.license_doc_url,
            photo_url=driver.photo_url,
            is_active=True
        )
        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)

        logger.info(f"Driver created successfully with driver_id={new_driver.driver_id}")
        return new_driver

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError while creating driver: {str(e.orig)}")
        raise HTTPException(status_code=400, detail="Integrity error while creating driver.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError while creating driver: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating driver.")

    except HTTPException as e:
        db.rollback()
        logger.warning(f"HTTPException: {e.detail}")
        raise e

    except Exception as e:
        db.rollback()
        logger.exception("Unexpected error while creating driver")
        raise HTTPException(status_code=500, detail="Unexpected error while creating driver.")