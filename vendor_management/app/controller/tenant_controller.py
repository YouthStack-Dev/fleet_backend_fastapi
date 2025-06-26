# from sqlalchemy.orm import Session
# from fastapi import HTTPException
# from app.api.schemas.schemas import TenantCreate
# from app.crud import crud

# class TenantController:
#     def create_tenant(self, tenant: TenantCreate, db: Session):
#         return crud.create_tenant(db, tenant)

#     def get_tenants(self, db: Session, skip: int = 0, limit: int = 100):
#         return crud.get_tenants(db, skip=skip, limit=limit)

#     def get_tenant(self, tenant_id: int, db: Session):
#         tenant = crud.get_tenant(db, tenant_id)
#         if not tenant:
#             raise HTTPException(status_code=404, detail="Tenant not found")
#         return tenant

#     def update_tenant(self, tenant_id: int, tenant_update: TenantCreate, db: Session):
#         updated = crud.update_tenant(db, tenant_id, tenant_update)
#         if not updated:
#             raise HTTPException(status_code=404, detail="Tenant not found")
#         return updated

#     def patch_tenant(self, tenant_id: int, tenant_update: dict, db: Session):
#         updated = crud.patch_tenant(db, tenant_id, tenant_update)
#         if not updated:
#             raise HTTPException(status_code=404, detail="Tenant not found")
#         return updated

#     def delete_tenant(self, tenant_id: int, db: Session):
#         deleted = crud.delete_tenant(db, tenant_id)
#         if not deleted:
#             raise HTTPException(status_code=404, detail="Tenant not found")
#         return deleted
