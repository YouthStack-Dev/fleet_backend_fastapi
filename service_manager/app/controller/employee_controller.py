from fastapi import HTTPException
from app.crud.crud import create_employee , get_employee as get_employee_service, update_employee, delete_employee , get_employee_by_department , bulk_create_employees,get_employee_by_tenant, update_employee_status
import traceback
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
class EmployeeController:


    def create_employee(self, employee, db, tenant_id):
        try:
            return create_employee(db, employee, tenant_id)
        except HTTPException as e:
            raise e
        except Exception :
            raise HTTPException(status_code=500, detail="Unexpected error occurred while creating employee.")

    def controller_bulk_create_employees(self, file, db, tenant_id):
        try:
            return bulk_create_employees(file, tenant_id, db)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while creating employees.")

    def get_employee(self, employee_code, db, tenant_id):
        try:
            return get_employee_service(db, employee_code, tenant_id)
        except HTTPException as e:
            logger.warning(f"HTTPException: {str(e.detail)}")
            raise e  # ✅ Re-raise the same HTTPException (404 or 409 etc.)
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Unhandled exception in controller: {str(e)}")
            raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching employee.")

    def get_employee_by_department(self, department_id, db, tenant_id, is_active, page, page_size):
        try:
            return get_employee_by_department(
                db=db,
                department_id=department_id,
                tenant_id=tenant_id,
                is_active=is_active,
                page=page,
                page_size=page_size
            )
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching employees.")

    def get_employee_by_tenant(self, db, tenant_id, page, limit):
        try:
            return get_employee_by_tenant(db, tenant_id, page, limit)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching employee.")

    def update_employee(self, employee_code, employee, db, tenant_id):
        try:
            return update_employee(db, employee_code, employee, tenant_id)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while updating employee.")
    def update_employee_status(self, employee_code, is_active, db, tenant_id):
        try:
            return update_employee_status(db, employee_code, is_active, tenant_id)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while updating employee status.")
        
    def delete_employee(self, employee_code, db, tenant_id):
        try:
            return delete_employee(db, employee_code, tenant_id)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while deleting employee.")
