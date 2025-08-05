from firebase_admin import db
from app.firebase.config import init_firebase

init_firebase()

def push_employee_to_firebase(tenant_id: int, department_id: int, employee_code: str, employee_id: int, name: str):
    ref_path = f"employees/{tenant_id}/{department_id}/{employee_code}"
    ref = db.reference(ref_path)
    print(f"Pushing employee data to Firebase at {ref_path}")
    print(f"Employee ID: {employee_id}, Employee Code: {employee_code}, Name: {name}")
    ref.set({
        "employee_id": employee_id,
        "employee_code": employee_code,
        "name": name
    })
