# department_controller.py
# from app.crud.crud import create_department, get_department_by_id, update_department_by_id, delete_department_by_id

# Controller (app/controllers/department_controller.py)
from app.crud.crud import create_department, get_departments, update_department, delete_department

class DepartmentController:
    def create_department(self, department, db, tenant_id):
        return create_department(db, department, tenant_id)

    def get_departments(self, db, tenant_id , skip=0, limit=100):
        return get_departments(db, tenant_id, skip, limit)

    def update_department(self, department_id, department, db, tenant_id):
        return update_department(db, department_id, department, tenant_id)

    def delete_department(self, department_id, db, tenant_id):
        return delete_department(db, department_id, tenant_id)

