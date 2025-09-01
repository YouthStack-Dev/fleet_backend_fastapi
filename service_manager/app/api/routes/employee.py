from typing import Optional
from venv import logger
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from app.database.models import Employee
from sqlalchemy.orm import Session
from app.api.schemas.schemas import EmployeeCreate, EmployeeRead, EmployeeStatusUpdate, EmployeeUpdate ,EmployeeDeleteRead, EmployeeUpdateResponse, EmployeesByDepartmentResponse, EmployeesByTenantResponse,EmployeeUpdateStatusResponse
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

@router.put("/{employee_code}/status", response_model=EmployeeUpdateStatusResponse)
async def update_employee_status(
    employee_code: str,
    payload: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.update"]))
):
    return controller.update_employee_status(
        employee_code=employee_code,
        is_active=payload.is_active,
        db=db,
        tenant_id=token_data["tenant_id"]
    )
    

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


@router.patch("/employees/{employee_id}/status", response_model=EmployeeUpdateResponse)
def toggle_employee_status(
    employee_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["employee_management.update"]))
):
    try:
        employee = (
            db.query(Employee)
            .filter(Employee.employee_id == employee_id)
            .first()
        )

        if not employee:
            logger.warning(f"Employee ID {employee_id} not found")
            raise HTTPException(status_code=404, detail="Employee not found")

        # ✅ Tenant check
        if employee.tenant_id != token_data["tenant_id"]:
            logger.warning(
                f"Tenant mismatch: user_tenant={token_data['tenant_id']} "
                f"employee_tenant={employee.tenant_id}"
            )
            raise HTTPException(status_code=403, detail="Not authorized for this employee")

        # Toggle status
        employee.is_active = not employee.is_active
        db.commit()
        db.refresh(employee)

        status = "activated" if employee.is_active else "deactivated"
        logger.info(f"Employee {employee_id} successfully {status} (tenant={employee.tenant_id})")
        return employee

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception(f"Error toggling status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



# @router.put("/{vendor_id}/drivers/{driver_id}/status", response_model=DriverOut)
# def update_driver_status(
#     vendor_id: int,
#     driver_id: int,
#     status: StatusUpdate,
#     db: Session = Depends(get_db),
#     token_data: dict = Depends(PermissionChecker(["driver_management.update"]))
# ):
#     try:
#         driver = db.query(Driver).filter_by(driver_id=driver_id, vendor_id=vendor_id).first()
#         if not driver:
#             logger.warning(f"Driver ID {driver_id} not found for vendor ID {vendor_id}")
#             raise HTTPException(status_code=404, detail="Driver not found for this vendor")

#         if driver.is_active == status.is_active:
#             current_state = "active" if status.is_active else "inactive"
#             logger.info(f"Driver {driver_id} is already {current_state}")
#             raise HTTPException(status_code=400, detail=f"Driver is already {current_state}")

#         driver.is_active = status.is_active
#         db.commit()
#         db.refresh(driver)

#         new_state = "activated" if driver.is_active else "deactivated"
#         logger.info(f"Driver {driver_id} under vendor {vendor_id} successfully {new_state}")
#         return driver

#     except HTTPException as http_exc:
#         raise http_exc  # Allow FastAPI to handle proper HTTPException responses
    
#     except Exception as e:
#         db.rollback()
#         logger.exception(f"Unexpected error while toggling driver status: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
