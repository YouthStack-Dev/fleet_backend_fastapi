# department_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.controller.department_controller import DepartmentController
from app.api.schemas.schemas import DepartmentCreate, DepartmentRead, DepartmentUpdate, DepartmentDeleteResponse, DepartmentWithCountResponse
from common_utils.auth.permission_checker import PermissionChecker
from typing import List



router = APIRouter()
controller = DepartmentController()

@router.post("/", response_model=DepartmentRead)
async def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["department_management.create"]))
):
    tenant_id = token_data["tenant_id"]
    return controller.create_department(department, db, tenant_id)


# @router.get("/{department_id}", response_model=DepartmentWithCountResponse)
# async def get_department(
#     department_id: int,
#     db: Session = Depends(get_db),
#     token_data: dict = Depends(PermissionChecker(["department_management.read"]))
# ):
#     tenant_id = token_data["tenant_id"]
#     department = controller.get_department(department_id, db, tenant_id, skip=0, limit=100)
#     if not department:
#         raise HTTPException(status_code=404, detail="Department not found")
#     return department


@router.get("/", response_model=List[DepartmentWithCountResponse])
async def get_departments(
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["department_management.read"])),
    skip: int = 0,
    limit: int = 100
):
    tenant_id = token_data["tenant_id"]
    return controller.get_departments(db, tenant_id, skip=skip, limit=limit)


@router.put("/{department_id}", response_model=DepartmentRead)
async def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["department_management.update"]))
):
    tenant_id = token_data["tenant_id"]
    department = controller.update_department(department_id, department_update, db, tenant_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.delete("/{department_id}", response_model=DepartmentDeleteResponse)
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["department_management.delete"]))
):
    tenant_id = token_data["tenant_id"]
    department = controller.delete_department(department_id, db, tenant_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department
