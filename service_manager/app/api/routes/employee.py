from typing import Optional
from uuid import uuid4
from venv import logger
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from app.database.models import Employee
from sqlalchemy.orm import Session
from app.api.schemas.schemas import EmployeeCreate, EmployeeRead, EmployeeStatusUpdate, EmployeeUpdate ,EmployeeDeleteRead, EmployeeUpdateResponse, EmployeesByDepartmentResponse, EmployeesByTenantResponse,EmployeeUpdateStatusResponse, Meta, EmployeeUpdate, StatusUpdate
from app.controller.employee_controller import EmployeeController
from app.database.database import get_db
from common_utils.auth.permission_checker import PermissionChecker

from app.utils.response import build_response

router = APIRouter()

controller = EmployeeController()

@router.post("/", response_model=EmployeeRead)
async def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.create"]))
):
    return controller.create_employee(employee, db, token_data["tenant_id"])
@router.post("/bulk")
def bulk_create_employee(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.create"]))
):
    return controller.controller_bulk_create_employees(file, db, token_data["tenant_id"])
@router.get("/department/{department_id}", response_model=EmployeesByDepartmentResponse)
async def get_employee(
    department_id: int,
    is_active: Optional[bool] = Query(None, description="Filter employees by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.read"]))
):
    return controller.get_employee_by_department(
        department_id=department_id,
        db=db,
        tenant_id=token_data["tenant_id"],
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

@router.get("/tenant", response_model=EmployeesByTenantResponse)
async def get_employee(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of bookings per page"),
    token_data: dict = Depends(PermissionChecker(["employee_management.read"]))
):
    return controller.get_employee_by_tenant(db, token_data["tenant_id"], page, limit)

@router.get("/{employee_code}", response_model=EmployeeRead)
async def get_employee(
    employee_code: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.read"]))
):
    # return controller.get_employee(employee_code, db, token_data["tenant_id"])
    print("🔵 Inside ROUTER")
    print(f"🔵 employee_code: {employee_code}, tenant_id: {token_data['tenant_id']}")
    return controller.get_employee(employee_code, db, token_data["tenant_id"])


    

@router.put("/{employee_code}", response_model=EmployeeUpdateResponse)
async def update_employee(
    employee_code: str,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.update"]))
):
    return controller.update_employee(employee_code, employee, db, token_data["tenant_id"])


@router.delete("/{employee_code}", response_model=EmployeeDeleteRead)
async def delete_employee(
    employee_code: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.delete"]))
):
    return controller.delete_employee(employee_code, db, token_data["tenant_id"])


from app.utils.decorators import handle_exceptions
from fastapi import Depends
from uuid import uuid4
@router.patch("/status/{employee_id}", response_model=EmployeeUpdateResponse)
@handle_exceptions
def toggle_employee_status(
    employee_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.update"]))
):
    # Only business logic here
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.tenant_id != token_data["tenant_id"]:
        raise HTTPException(status_code=403, detail="Not authorized for this employee")

    # Toggle status
    employee.is_active = not employee.is_active
    db.commit()
    db.refresh(employee)

    status_text = "activated" if employee.is_active else "deactivated"
    logger.info(f"Employee {employee_id} successfully {status_text} (tenant={employee.tenant_id})")

    return build_response(
        data=EmployeeUpdate.model_validate(employee, from_attributes=True),
        message=f"Employee {status_text} successfully",
        code=200,
        status="success"
    )




@router.put("/status/{employee_id}", response_model=EmployeeUpdateResponse)
@handle_exceptions
def update_employee_status(
    employee_id: int,
    status: StatusUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.update"]))
):
    """
    Updates the employee status explicitly to the given value.
    Only business logic here; errors are handled by the decorator.
    """
    employee = db.query(Employee).filter_by(employee_id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.tenant_id != token_data["tenant_id"]:
        raise HTTPException(status_code=403, detail="Not authorized for this employee")

    if employee.is_active == status.is_active:
        current_state = "active" if status.is_active else "inactive"
        raise HTTPException(status_code=400, detail=f"Employee is already {current_state}")

    # Update status
    employee.is_active = status.is_active
    db.commit()
    db.refresh(employee)

    new_state = "activated" if employee.is_active else "deactivated"
    logger.info(f"Employee {employee_id} successfully {new_state} (tenant={employee.tenant_id})")

    return build_response(
        data=EmployeeUpdate.model_validate(employee, from_attributes=True),
        message=f"Employee {new_state} successfully",
        code=200,
        status="success"
    )