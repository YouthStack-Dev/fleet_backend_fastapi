# from sqlalchemy.orm import Session
# from fastapi import HTTPException
# from sqlalchemy.exc import IntegrityError
# from app.crud import crud

# class MappingController:
#     # User-Tenant Mapping
#     def add_user_tenant(self, user_id: int, tenant_id: int, metadata: dict, db: Session):
#         try:
#             return crud.add_user_tenant(db, user_id, tenant_id, metadata)
#         except IntegrityError:
#             db.rollback()
#             raise HTTPException(status_code=409, detail="User-Tenant mapping already exists")

#     def list_user_tenants(self, db: Session):
#         rows = crud.list_user_tenants(db)
#         return [dict(row._mapping) for row in rows]

#     def remove_user_tenant(self, user_id: int, tenant_id: int, db: Session):
#         return crud.remove_user_tenant(db, user_id, tenant_id)

#     # Group-Role Mapping
#     def add_group_role(self, group_id: int, role_id: int, db: Session):
#         try:
#             return crud.add_group_role(db, group_id, role_id)
#         except IntegrityError:
#             db.rollback()
#             raise HTTPException(status_code=409, detail="Group-Role mapping already exists")

#     def list_group_roles(self, db: Session):
#         rows = crud.list_group_roles(db)
#         return [dict(row._mapping) for row in rows]

#     def remove_group_role(self, group_id: int, role_id: int, db: Session):
#         return crud.remove_group_role(db, group_id, role_id)

#     # User-Role Mapping
#     def add_user_role(self, user_id: int, role_id: int, tenant_id: int, db: Session):
#         try:
#             return crud.add_user_role(db, user_id, role_id, tenant_id)
#         except IntegrityError:
#             db.rollback()
#             raise HTTPException(status_code=409, detail="User-Role mapping already exists")

#     def list_user_roles(self, db: Session):
#         rows = crud.list_user_roles(db)
#         return [dict(row._mapping) for row in rows]

#     def remove_user_role(self, user_id: int, role_id: int, tenant_id: int, db: Session):
#         return crud.remove_user_role(db, user_id, role_id, tenant_id)

#     # Group-User Mapping
#     def add_group_user(self, group_id: int, user_id: int, db: Session):
#         try:
#             return crud.add_group_user(db, group_id, user_id)
#         except IntegrityError:
#             db.rollback()
#             raise HTTPException(status_code=409, detail="Group-User mapping already exists")

#     def list_group_users(self, db: Session):
#         rows = crud.list_group_users(db)
#         return [dict(row._mapping) for row in rows]

#     def remove_group_user(self, group_id: int, user_id: int, db: Session):
#         return crud.remove_group_user(db, group_id, user_id)
