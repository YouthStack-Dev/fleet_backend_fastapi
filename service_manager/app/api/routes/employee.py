from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.schemas.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate ,EmployeeDeleteRead
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


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.read"]))
):
    return controller.get_employee(employee_id, db, token_data["tenant_id"])


@router.put("/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.update"]))
):
    return controller.update_employee(employee_id, employee, db, token_data["tenant_id"])


@router.delete("/{employee_id}", response_model=EmployeeDeleteRead)
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.delete"]))
):
    return controller.delete_employee(employee_id, db, token_data["tenant_id"])
