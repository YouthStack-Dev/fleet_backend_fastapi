# app/controller/vendor_controller.py

from app.crud.crud import create_vendor, get_vendors, get_vendor_by_id , update_vendor, delete_vendor
from fastapi import HTTPException
class VendorController:
    def create_vendor(self, db, tenant_id, user_id, vendor_data):
        vendor = create_vendor(db, vendor_data, tenant_id)
        return vendor

    def get_vendors(self, db, tenant_id, skip: int, limit: int):
        try:
            vendors = get_vendors(db, tenant_id, skip, limit)
            return vendors
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch vendors.")
    def get_vendor_by_id(self, db, tenant_id: int, vendor_id: int):
        try:
            return get_vendor_by_id(db, tenant_id, vendor_id)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch vendor")
        
    def update_vendor(self, db, tenant_id, vendor_id, update_data, user_id):
        try:
            vendor = update_vendor(db, tenant_id, vendor_id, update_data)
            return vendor
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to update vendor")
    def delete_vendor(self, db, tenant_id: int, vendor_id: int, user_id: int):
        try:
            return delete_vendor(db, tenant_id, vendor_id, user_id)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to delete vendor")