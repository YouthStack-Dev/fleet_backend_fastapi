import io
import logging
import os
import shutil
from typing import Optional
from fastapi import HTTPException, Response, UploadFile
import traceback
from fastapi import APIRouter, Depends, status, Form, UploadFile, File, HTTPException, Request
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import VehicleOut
from app.database.models import Driver, Vehicle, Vendor
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import uuid4
from typing import Annotated, Optional
from datetime import date
import os
import shutil
import logging
from common_utils.auth.permission_checker import PermissionChecker
# services/driver_service.py or similar
from common_utils.auth.utils import hash_password
from typing import Callable, Optional
import io
from sqlalchemy import func, or_
from fastapi import Query
from typing import List, Optional
from sqlalchemy.orm import selectinload
router = APIRouter()
from sqlalchemy.orm import joinedload


logger = logging.getLogger(__name__)
async def file_size_validator(
    file: Optional[UploadFile],
    allowed_types: list[str],
    max_size_mb: int = 5
) -> Optional[UploadFile]:
    if not file or not file.filename:
        logger.info("No file uploaded, skipping validation.")
        return None

    logger.info(f"Validating file: {file.filename}")

    if file.content_type not in allowed_types:
        logger.warning(f"{file.filename} has invalid type '{file.content_type}'. Allowed types: {allowed_types}")
        raise HTTPException(
            status_code=415,
            detail=f"{file.filename} has invalid type '{file.content_type}'. Allowed types: {allowed_types}"
        )

    contents = await file.read()
    file.file = io.BytesIO(contents)  # reset file pointer

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"{file.filename} is too large. Max allowed size is {max_size_mb}MB."
        )

    return file
def save_file(
    file: Optional[UploadFile],
    vendor_id: int,
    vehicle_code: str,
    doc_type: str
) -> Optional[str]:
    if file and file.filename:
        # Get file extension from original filename
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower().strip()  # normalize extension

        # Construct safe filename: {vehicle_code}_{doc_type}.{ext}
        safe_filename = f"{vehicle_code.strip()}_{doc_type.strip()}{ext}"

        # New path: uploaded_files/vendors/{vendor_id}/vehicles/{vehicle_code}/{doc_type}/{filename}
        folder_path = os.path.join("uploaded_files", "vendors", str(vendor_id), "vehicles", vehicle_code.strip(), doc_type)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, safe_filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        rel_path = os.path.relpath(file_path, start="uploaded_files")
        abs_path = os.path.abspath(file_path)

        logger.info(f"{doc_type.upper()} document saved at: {abs_path}")
        return rel_path
    else:
        logger.debug(f"No file provided for {doc_type}")
    return None

from datetime import datetime

def parse_date(date_str: Optional[str]) -> Optional[date]:
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD.")
    return None

@router.post("/{vendor_id}/vehicles/",response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    request: Request,
    vendor_id: int,
    vehicle_code: str = Form(...),
    reg_number: str = Form(...),
    vehicle_type_id: int = Form(...),
    status: str = Form(...),
    description: Optional[str] = Form(None),

    driver_id: Optional[int] = Form(None),

    rc_expiry_date: Optional[date] = Form(None),
    insurance_expiry_date: Optional[date] = Form(None),
    permit_expiry_date: Optional[date] = Form(None),
    pollution_expiry_date: Optional[date] = Form(None),
    fitness_expiry_date: Optional[date] = Form(None),
    tax_receipt_date: Optional[date] = Form(None),

    rc_card_file: Optional[UploadFile] = File(None),
    insurance_file: Optional[UploadFile] = File(None),
    permit_file: Optional[UploadFile] = File(None),
    pollution_file: Optional[UploadFile] = File(None),
    fitness_file: Optional[UploadFile] = File(None),
    tax_receipt_file: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vehicle_management.create"]))
):
    form = await request.form()
    print("Received form:", form)
    tenant_id = token_data.get("tenant_id")
    try:
        logger.info(f"Creating vehicle: vendor_id={vendor_id}, code={vehicle_code}")
        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id, tenant_id=tenant_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found or does not belong to tenant.")

        # Uniqueness checks
        if db.query(Vehicle).filter_by(vehicle_code=vehicle_code.strip(), vendor_id=vendor_id).first():
            raise HTTPException(status_code=409, detail="Vehicle code already exists.")

        if db.query(Vehicle).filter_by(reg_number=reg_number.strip(), vendor_id=vendor_id).first():
            raise HTTPException(status_code=409, detail="Registration number already exists.")

        if status.strip().upper() not in {"ACTIVE", "INACTIVE"}:
            raise HTTPException(status_code=400, detail="Invalid status value.")
        # Check if driver is already assigned to another vehicle
        if driver_id is not None:
            existing_assignment = db.query(Vehicle).filter_by(driver_id=driver_id).first()
            if existing_assignment:
                raise HTTPException(
                    status_code=409,
                    detail=f"Driver is already assigned to vehicle with ID {existing_assignment.vehicle_id} (code: {existing_assignment.vehicle_code})."
                )

        async def process_file(doc_file, doc_type, allowed_types, vehicle_code):
            if doc_file:
                validated = await file_size_validator(doc_file, allowed_types=allowed_types)
                return  save_file(doc_file, vendor_id, vehicle_code, doc_type)
            return None
        # Save documents
        rc_card_url = await process_file(rc_card_file, "rc_card", allowed_types=["application/pdf"], vehicle_code=vehicle_code)
        permit_url = await process_file(permit_file, "permit", allowed_types=["application/pdf"], vehicle_code=vehicle_code)
        tax_receipt_url = await process_file(tax_receipt_file, "tax_receipt", allowed_types=["application/pdf"], vehicle_code=vehicle_code)
        insurance_url = await process_file(insurance_file, "insurance", allowed_types=["application/pdf"], vehicle_code=vehicle_code)
        pollution_url = await process_file(pollution_file, "pollution", allowed_types=["application/pdf"], vehicle_code=vehicle_code)
        fitness_url = await process_file(fitness_file, "fitness", allowed_types=["application/pdf"], vehicle_code=vehicle_code)


        # Create Vehicle object
        new_vehicle = Vehicle(
            vendor_id=vendor_id,
            vehicle_code=vehicle_code.strip(),
            reg_number=reg_number.strip(),
            vehicle_type_id=vehicle_type_id,
            driver_id=driver_id,
            status=status.strip(),
            description=description,

            rc_card_url=rc_card_url,
            insurance_url=insurance_url,
            permit_url=permit_url,
            pollution_url=pollution_url,
            fitness_url=fitness_url,
            tax_receipt_url=tax_receipt_url,

            # These fields can be added in model if needed
            rc_expiry_date=rc_expiry_date,
            insurance_expiry_date=insurance_expiry_date,
            permit_expiry_date=permit_expiry_date,
            pollution_expiry_date=pollution_expiry_date,
            fitness_expiry_date=fitness_expiry_date,
            tax_receipt_date=tax_receipt_date,
        )

        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)

        logger.info(f"Vehicle {vehicle_code} created successfully.")
        return new_vehicle

    except IntegrityError as e:
        db.rollback()
        # Extract foreign key violation or uniqueness issue
        if "vehicles_driver_id_fkey" in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="Invalid driver_id: Driver does not exist."
            )
        raise HTTPException(
            status_code=400,
            detail=f"Integrity error: {str(e.orig)}"
        )
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {str(e.orig)}")
        raise HTTPException(status_code=400, detail="Integrity error while creating vehicle.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating vehicle.")
    except HTTPException as e:
        db.rollback()
        logger.warning(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        db.rollback()
        logger.exception("Unhandled error in driver creation: %s", str(e))
        traceback.print_exc()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while creating vehicle.")

@router.put("/{vendor_id}/vehicles/{vehicle_id}/", response_model=VehicleOut)
async def update_vehicle(
    request: Request,
    vendor_id: int,
    vehicle_id: int,
    vehicle_code: str = Form(...),
    reg_number: str = Form(...),
    vehicle_type_id: int = Form(...),
    status: str = Form(...),
    description: Optional[str] = Form(None),

    driver_id: Optional[int] = Form(None),

    rc_expiry_date: Optional[date] = Form(None),
    insurance_expiry_date: Optional[date] = Form(None),
    permit_expiry_date: Optional[date] = Form(None),
    pollution_expiry_date: Optional[date] = Form(None),
    fitness_expiry_date: Optional[date] = Form(None),
    tax_receipt_date: Optional[date] = Form(None),

    rc_card_file: Optional[UploadFile] = File(None),
    insurance_file: Optional[UploadFile] = File(None),
    permit_file: Optional[UploadFile] = File(None),
    pollution_file: Optional[UploadFile] = File(None),
    fitness_file: Optional[UploadFile] = File(None),
    tax_receipt_file: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vehicle_management.update"]))
):
    tenant_id = token_data.get("tenant_id")
    try:
        logger.info(f"Updating vehicle_id={vehicle_id} for vendor_id={vendor_id}")

        # Fetch vehicle
        vehicle = (
            db.query(Vehicle)
            .filter_by(vehicle_id=vehicle_id, vendor_id=vendor_id)
            .first()
        )
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found.")

        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id, tenant_id=tenant_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found or unauthorized.")

        # Uniqueness checks for update
        if (
            db.query(Vehicle)
            .filter(Vehicle.vehicle_code == vehicle_code.strip(), Vehicle.vendor_id == vendor_id, Vehicle.vehicle_id != vehicle_id)
            .first()
        ):
            raise HTTPException(status_code=409, detail="Vehicle code already exists.")

        if (
            db.query(Vehicle)
            .filter(Vehicle.reg_number == reg_number.strip(), Vehicle.vendor_id == vendor_id, Vehicle.vehicle_id != vehicle_id)
            .first()
        ):
            raise HTTPException(status_code=409, detail="Registration number already exists.")

        if status.strip().upper() not in {"ACTIVE", "INACTIVE"}:
            raise HTTPException(status_code=400, detail="Invalid status value.")

        # Driver assignment check
        if driver_id is not None:
            existing_assignment = (
                db.query(Vehicle)
                .filter(Vehicle.driver_id == driver_id, Vehicle.vehicle_id != vehicle_id)
                .first()
            )
            if existing_assignment:
                raise HTTPException(
                    status_code=409,
                    detail=f"Driver is already assigned to another vehicle: {existing_assignment.vehicle_code}",
                )

        # File processing helper
        async def process_file(doc_file, doc_type, allowed_types, vehicle_code):
            if doc_file:
                validated = await file_size_validator(doc_file, allowed_types=allowed_types)
                return save_file(doc_file, vendor_id, vehicle_code, doc_type)
            return None

        # Update fields
        vehicle.vehicle_code = vehicle_code.strip()
        vehicle.reg_number = reg_number.strip()
        vehicle.vehicle_type_id = vehicle_type_id
        vehicle.driver_id = driver_id
        vehicle.status = status.strip()
        vehicle.description = description

        vehicle.rc_expiry_date = rc_expiry_date
        vehicle.insurance_expiry_date = insurance_expiry_date
        vehicle.permit_expiry_date = permit_expiry_date
        vehicle.pollution_expiry_date = pollution_expiry_date
        vehicle.fitness_expiry_date = fitness_expiry_date
        vehicle.tax_receipt_date = tax_receipt_date

        # Update documents only if new ones provided
        rc_card_url = await process_file(rc_card_file, "rc_card", ["application/pdf"], vehicle_code)
        if rc_card_url:
            vehicle.rc_card_url = rc_card_url

        insurance_url = await process_file(insurance_file, "insurance", ["application/pdf"], vehicle_code)
        if insurance_url:
            vehicle.insurance_url = insurance_url

        permit_url = await process_file(permit_file, "permit", ["application/pdf"], vehicle_code)
        if permit_url:
            vehicle.permit_url = permit_url

        pollution_url = await process_file(pollution_file, "pollution", ["application/pdf"], vehicle_code)
        if pollution_url:
            vehicle.pollution_url = pollution_url

        fitness_url = await process_file(fitness_file, "fitness", ["application/pdf"], vehicle_code)
        if fitness_url:
            vehicle.fitness_url = fitness_url

        tax_receipt_url = await process_file(tax_receipt_file, "tax_receipt", ["application/pdf"], vehicle_code)
        if tax_receipt_url:
            vehicle.tax_receipt_url = tax_receipt_url

        db.commit()
        db.refresh(vehicle)

        logger.info(f"Vehicle {vehicle_code} updated successfully.")
        return vehicle

    except IntegrityError as e:
        db.rollback()
        if "vehicles_driver_id_fkey" in str(e.orig):
            raise HTTPException(status_code=400, detail="Invalid driver_id.")
        logger.error(f"IntegrityError: {str(e.orig)}")
        raise HTTPException(status_code=400, detail="Integrity error while updating vehicle.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating vehicle.")
    except HTTPException as e:
        db.rollback()
        logger.warning(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        db.rollback()
        logger.exception("Unhandled error in vehicle update: %s", str(e))
        raise HTTPException(status_code=500, detail="Unexpected error while updating vehicle.")

@router.get("/vehicles/", response_model=List[VehicleOut])
def get_vehicles(
    vendor_id: Optional[int] = Query(None),
    driver_id: Optional[int] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    vehicle_code: Optional[str] = Query(None),
    vehicle_type_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),  # ACTIVE / INACTIVE

    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),

    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vehicle_management.read"]))
):
    tenant_id = token_data.get("tenant_id")

    try:
        logger.info("Fetching vehicles with filters: "
                    f"tenant_id={tenant_id}, vendor_id={vendor_id}, driver_id={driver_id}, "
                    f"vehicle_id={vehicle_id}, vehicle_code={vehicle_code}, vehicle_type_id={vehicle_type_id}, "
                    f"status={status}, limit={limit}, offset={offset}")

        query = db.query(Vehicle).join(Vendor).filter(Vendor.tenant_id == tenant_id)

        # Apply filters
        if vendor_id is not None:
            query = query.filter(Vehicle.vendor_id == vendor_id)

        if driver_id is not None:
            query = query.filter(Vehicle.driver_id == driver_id)

        if vehicle_id is not None:
            query = query.filter(Vehicle.vehicle_id == vehicle_id)

        if vehicle_code is not None:
            query = query.filter(Vehicle.vehicle_code.ilike(f"%{vehicle_code.strip()}%"))

        if vehicle_type_id is not None:
            query = query.filter(Vehicle.vehicle_type_id == vehicle_type_id)

        if status:
            query = query.filter(func.lower(Vehicle.status) == status.strip().lower())


        total = query.count()
        vehicles = query.offset(offset).limit(limit).all()

        if not vehicles:
            logger.warning("No vehicles found for given filters.")
            raise HTTPException(status_code=404, detail="No vehicles found for the given filters.")     
           
        logger.info(f"Found {len(vehicles)} of {total} total vehicles matching filters.")
        return vehicles
    except HTTPException as e:
        logger.warning(f"HTTPException: {e.detail}")
        raise e  # DO NOT LOG AGAIN IN GENERAL EXCEPTION
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError while fetching vehicles: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching vehicles.")

    except Exception as e:
        logger.exception("Unhandled error while fetching vehicles")
        raise HTTPException(status_code=500, detail="Unexpected error while fetching vehicles.")

from fastapi.responses import JSONResponse

@router.delete("/{vendor_id}/vehicles/{vehicle_id}/", response_class=JSONResponse, status_code=status.HTTP_200_OK)
def delete_vehicle(
    vendor_id: int,
    vehicle_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vehicle_management.delete"]))
):
    tenant_id = token_data.get("tenant_id")
    try:
        logger.info(f"Attempting to delete vehicle_id={vehicle_id} for vendor_id={vendor_id}, tenant_id={tenant_id}")

        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id, tenant_id=tenant_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found or unauthorized.")

        vehicle = db.query(Vehicle).filter_by(vehicle_id=vehicle_id, vendor_id=vendor_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found.")

        db.delete(vehicle)
        db.commit()

        logger.info(f"Vehicle with ID {vehicle_id} deleted successfully.")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Vehicle deleted successfully",
                "vehicle_id": vehicle_id
            }
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemy error while deleting vehicle: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while deleting vehicle.")
    except HTTPException as e:
        logger.warning(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        db.rollback()
        logger.exception("Unhandled error during vehicle deletion")
        raise HTTPException(status_code=500, detail="Unexpected error while deleting vehicle.")
