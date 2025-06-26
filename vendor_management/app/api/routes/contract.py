# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.database.database import get_db
# from app.api.routes.auth import get_token_payload, token_dependency
# from app.controller.mapping_controller import MappingController

# router = APIRouter()
# mapping_controller = MappingController()

# # User-Tenant Mapping
# @router.post("/user_tenant/")
# def add_user_tenant(
#     token: token_dependency,
#     user_id: int,
#     tenant_id: int,
#     metadata: dict = None,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.add_user_tenant(user_id, tenant_id, metadata, db)

# @router.get("/user_tenant/")
# def list_user_tenants(
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.list_user_tenants(db)

# @router.delete("/user_tenant/")
# def remove_user_tenant(
#     user_id: int,
#     tenant_id: int,
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.remove_user_tenant(user_id, tenant_id, db)

# # Group-Role Mapping
# @router.post("/group_role/")
# def add_group_role(
#     group_id: int,
#     role_id: int,
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.add_group_role(group_id, role_id, db)

# @router.get("/group_role/")
# def list_group_roles(
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.list_group_roles(db)

# @router.delete("/group_role/")
# def remove_group_role(
#     group_id: int,
#     role_id: int,
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.remove_group_role(group_id, role_id, db)

# # User-Role Mapping
# @router.post("/user_role/")
# def add_user_role(
#     user_id: int,
#     role_id: int,
#     tenant_id: int,
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.add_user_role(user_id, role_id, tenant_id, db)

# @router.get("/user_role/")
# def list_user_roles(
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.list_user_roles(db)

# @router.delete("/user_role/")
# def remove_user_role(
#     user_id: int,
#     role_id: int,
#     tenant_id: int,
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.remove_user_role(user_id, role_id, tenant_id, db)

# # Group-User Mapping
# @router.post("/group_user/")
# def add_group_user(
#     group_id: int,
#     user_id: int,
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.add_group_user(group_id, user_id, db)

# @router.get("/group_user/")
# def list_group_users(
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.list_group_users(db)

# @router.delete("/group_user/")
# def remove_group_user(
#     group_id: int,
#     user_id: int,
#     token: token_dependency,
#     db: Session = Depends(get_db)
# ):
#     return mapping_controller.remove_group_user(group_id, user_id, db)
