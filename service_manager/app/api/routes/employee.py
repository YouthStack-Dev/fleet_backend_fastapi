from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from app.api.schemas.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate ,EmployeeDeleteRead, EmployeeUpdateResponse, EmployeesByDepartmentResponse, EmployeesByTenantResponse
from app.controller.employee_controller import EmployeeController
from app.database.database import get_db
from common_utils.auth.permission_checker import PermissionChecker

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
