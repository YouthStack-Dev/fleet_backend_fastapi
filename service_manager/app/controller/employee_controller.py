from fastapi import HTTPException
from app.crud.crud import create_employee , get_employee, update_employee, delete_employee

class EmployeeController:


    def create_employee(self, employee, db, tenant_id):
        return create_employee(db, employee, tenant_id)


    def get_employee(self, employee_id, db, tenant_id):
        try:
            return get_employee(db, employee_id, tenant_id)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching employee.")

    def update_employee(self, employee_id, employee, db, tenant_id):
        try:
            return update_employee(db, employee_id, employee, tenant_id)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while updating employee.")

    def delete_employee(self, employee_id, db, tenant_id):
        try:
            return delete_employee(db, employee_id, tenant_id)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Unexpected error occurred while deleting employee.")
