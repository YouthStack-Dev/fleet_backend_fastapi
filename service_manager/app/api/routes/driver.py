import traceback
from fastapi import APIRouter, Depends, status, Form, UploadFile, File, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import DriverCreate, DriverOut, DriverUpdate,StatusUpdate
from app.database.models import Driver, User, Vendor
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
from sqlalchemy import or_
from fastapi import Query
from typing import List, Optional
from sqlalchemy.orm import selectinload
logger = logging.getLogger(__name__)
router = APIRouter()
from sqlalchemy.orm import joinedload

@router.get("/tenants/drivers/", response_model=List[DriverOut])
def get_all_drivers_by_tenant(
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["driver_management.read"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500)
) -> List[DriverOut]:
    tenant_id = token_data.get("tenant_id")
    logger.info(f"[DRIVER_FETCH] Start - tenant_id={tenant_id}, skip={skip}, limit={limit}")

    try:
        drivers = (
            db.query(Driver)
            .join(Driver.vendor)
            .filter(Vendor.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.info(f"[DRIVER_FETCH] Success - tenant_id={tenant_id}, count={len(drivers)}")
        return [DriverOut.model_validate(driver) for driver in drivers]

    except SQLAlchemyError as db_err:
        logger.exception(f"[DRIVER_FETCH] DB error - tenant_id={tenant_id}, error={db_err}")
        raise HTTPException(status_code=500, detail="Database error while fetching drivers.")

    except Exception as err:
        logger.exception(f"[DRIVER_FETCH] Unexpected error - tenant_id={tenant_id}, error={err}")
        raise HTTPException(status_code=500, detail="Unexpected server error.")

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
    driver_code: str,
    doc_type: str
) -> Optional[str]:
    if file and file.filename:
        # Get file extension from original filename
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower().strip()  # normalize extension

        # Construct safe filename: {driver_code}_{doc_type}.{ext}
        safe_filename = f"{driver_code.strip()}_{doc_type.strip()}{ext}"

        # New path: uploaded_files/vendors/{vendor_id}/drivers/{driver_code}/{doc_type}/{filename}
        folder_path = os.path.join("uploaded_files", "vendors", str(vendor_id), "drivers", driver_code.strip(), doc_type)
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

@router.post("/{vendor_id}/drivers/", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
async def create_driver(
    vendor_id: int,
    # form_data: DriverCreate = Depends(),
    driver_code: str = Form(...),
    name: str = Form(...),
    email: EmailStr = Form(...),
    hashed_password: str = Form(...),
    mobile_number: str = Form(...),

    city: Optional[str] = Form(...),
    date_of_birth: Optional[date] = Form(...),
    gender: Optional[str] = Form(...),

    alternate_mobile_number: Optional[str] = Form(...),
    permanent_address: Optional[str] = Form(...),
    current_address: Optional[str] = Form(...),

    bgv_status: Optional[str] = Form(...),
    bgv_date: Optional[date] = Form(...),

    police_verification_status: Optional[str] = Form(...),
    police_verification_date: Optional[date] = Form(...),

    medical_verification_status: Optional[str] = Form(...),
    medical_verification_date: Optional[date] = Form(...),

    training_verification_status: Optional[str] = Form(...),
    training_verification_date: Optional[date] = Form(...),

    eye_test_verification_status: Optional[str] = Form(...),
    eye_test_verification_date: Optional[date] = Form(...),

    license_number: Optional[str] = Form(...),
    license_expiry_date: Optional[date] = Form(...),

    induction_date: Optional[date] = Form(...),

    badge_number: Optional[str] = Form(...),
    badge_expiry_date: Optional[date] = Form(...),

    alternate_govt_id: Optional[str] = Form(...),
    alternate_govt_id_doc_type: Optional[str] = Form(...),

    bgv_doc_file: Optional[UploadFile] = None,
    police_verification_doc_file: Optional[UploadFile] = None,
    medical_verification_doc_file: Optional[UploadFile] = None,
    training_verification_doc_file: Optional[UploadFile] = None,
    eye_test_verification_doc_file: Optional[UploadFile] = None,
    license_doc_file: Optional[UploadFile] = None,
    induction_doc_file: Optional[UploadFile] = None,
    badge_doc_file: Optional[UploadFile] = None,
    alternate_govt_id_doc_file: Optional[UploadFile] = None,
    photo_image: Optional[UploadFile] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["driver_management.create"]))
):

    try:
        logger.info(f"Creating driver for vendor_id={vendor_id} with email={email}")
        logger.info(f"Received form data: bgv_doc_file: {bgv_doc_file.filename if bgv_doc_file else 'None'},police_verification_doc_file: {police_verification_doc_file.filename if police_verification_doc_file else 'None'},medical_verification_doc_file: {medical_verification_doc_file.filename if medical_verification_doc_file else 'None'}, training_verification_doc_file: {training_verification_doc_file.filename if training_verification_doc_file else 'None'}, eye_test_verification_doc_file: {eye_test_verification_doc_file.filename if eye_test_verification_doc_file else 'None'}, license_doc_file: {license_doc_file.filename if license_doc_file else 'None'}, induction_doc_file: {induction_doc_file.filename if induction_doc_file else 'None'}, badge_doc_file: {badge_doc_file.filename if badge_doc_file else 'None'}, alternate_govt_id_doc_file: {alternate_govt_id_doc_file.filename if alternate_govt_id_doc_file else 'None'}, photo_image: {photo_image.filename if photo_image else 'None'}")

       # Validate file sizes if present
        # For PDF documents
        bgv_doc_file = await file_size_validator(bgv_doc_file, allowed_types=["application/pdf"])
        police_verification_doc_file = await file_size_validator(police_verification_doc_file, allowed_types=["application/pdf"])
        medical_verification_doc_file = await file_size_validator(medical_verification_doc_file, allowed_types=["application/pdf"])
        training_verification_doc_file = await file_size_validator(training_verification_doc_file, allowed_types=["application/pdf"])
        eye_test_verification_doc_file = await file_size_validator(eye_test_verification_doc_file, allowed_types=["application/pdf"])
        license_doc_file = await file_size_validator(license_doc_file, allowed_types=["application/pdf"])
        induction_doc_file = await file_size_validator(induction_doc_file, allowed_types=["application/pdf"])
        badge_doc_file = await file_size_validator(badge_doc_file, allowed_types=["application/pdf"])
        alternate_govt_id_doc_file = await file_size_validator(alternate_govt_id_doc_file, allowed_types=["application/pdf"])

        # For photo image (jpeg/png)
        photo_image = await file_size_validator(
            photo_image,
            allowed_types=["image/jpeg", "image/jpg", "image/png"]
        )


        # Log what files were uploaded
        logger.info("Files uploaded:")
        for label, file in {
            "bgv": bgv_doc_file,
            "police": police_verification_doc_file,
            "medical": medical_verification_doc_file,
            "training": training_verification_doc_file,
            "eye": eye_test_verification_doc_file,
            "license": license_doc_file,
            "induction": induction_doc_file,
            "badge": badge_doc_file,
            "govt_id": alternate_govt_id_doc_file,
            "photo": photo_image,
        }.items():
            if file:
                logger.info(f"{label}: {file.filename} ({len(await file.read()) / (1024 * 1024):.2f} MB)")
                file.file.seek(0)  # Reset after reading for logging



        # Validation
        if not name.strip():
            raise HTTPException(status_code=422, detail="Name is required.")
        if not driver_code.strip():
            raise HTTPException(status_code=422, detail="Driver code is required.")
        if not email.strip():
            raise HTTPException(status_code=422, detail="Email is required.")
        if '@' not in email:
            raise HTTPException(status_code=422, detail="Invalid email format.")
        if not mobile_number.strip():
            raise HTTPException(status_code=422, detail="Mobile number is required.")
        if len(mobile_number) > 15:
            raise HTTPException(status_code=422, detail="Mobile number too long.")
        if not hashed_password.strip():
            raise HTTPException(status_code=422, detail="Password is required.")

        # Vendor Check
        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")

    # Check if vendor exists
        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")
        
        # Uniqueness Checks in drivers table
        if db.query(Driver).filter_by(email=email.strip()).first():
            raise HTTPException(status_code=409, detail="Email already exists.")
        
        if db.query(Driver).filter_by(mobile_number=mobile_number.strip()).first():
            raise HTTPException(status_code=409, detail="Mobile number already exists.")
        if db.query(Driver).filter_by(vendor_id=vendor_id, driver_code=driver_code.strip()).first():
            raise HTTPException(status_code=409, detail=f"Driver code '{driver_code}' already exists for this vendor.")

        bgv_doc_url = save_file(bgv_doc_file, vendor_id, driver_code, "bgv")
        if bgv_doc_url:
            logger.info(f"BGV document saved at: {bgv_doc_url}")
        police_verification_doc_file_url = save_file(police_verification_doc_file, vendor_id, driver_code, "police_verification")
        if police_verification_doc_file_url:
            logger.info(f"Police verification document saved at: {police_verification_doc_file_url}")
        medical_verification_doc_file_url = save_file(medical_verification_doc_file, vendor_id, driver_code, "medical_verification")
        if medical_verification_doc_file_url:
            logger.info(f"Medical verification document saved at: {medical_verification_doc_file_url}")
        training_verification_doc_file_url = save_file(training_verification_doc_file, vendor_id, driver_code, "training_verification")
        if training_verification_doc_file_url:
            logger.info(f"Training verification document saved at: {training_verification_doc_file_url}")
        eye_test_verification_doc_file_url = save_file(eye_test_verification_doc_file, vendor_id, driver_code, "eye_test_verification")
        if eye_test_verification_doc_file_url:
            logger.info(f"Eye test verification document saved at: {eye_test_verification_doc_file_url}")
        license_doc_file_url = save_file(license_doc_file, vendor_id, driver_code, "license")
        if license_doc_file_url:
            logger.info(f"License document saved at: {license_doc_file_url}")
        induction_doc_file_url = save_file(induction_doc_file, vendor_id, driver_code, "induction")
        if induction_doc_file_url:
            logger.info(f"Induction document saved at: {induction_doc_file_url}")
        badge_doc_file_url = save_file(badge_doc_file, vendor_id, driver_code, "badge")
        if badge_doc_file_url:
            logger.info(f"Badge document saved at: {badge_doc_file_url}")
        alternate_govt_id_doc_file_url = save_file(alternate_govt_id_doc_file, vendor_id, driver_code, "alternate_govt_id")
        if alternate_govt_id_doc_file_url:
            logger.info(f"Alternate government ID document saved at: {alternate_govt_id_doc_file_url}")
        photo_image_url = save_file(photo_image, vendor_id, driver_code, "photo")
        if photo_image_url:
            logger.info(f"Photo image saved at: {photo_image_url}")

        # Create Driver
        new_driver = Driver(
            name=name.strip(),
            email=email.strip(),
            driver_code=driver_code.strip(),
            mobile_number=mobile_number.strip(),
            hashed_password=hash_password(hashed_password.strip()),
            vendor_id=vendor_id,
            alternate_mobile_number=alternate_mobile_number,
            city=city,
            date_of_birth=date_of_birth,
            gender=gender,
            permanent_address=permanent_address,
            current_address=current_address,
            photo_url=photo_image_url,

            # ✅ BGV
            bgv_status=bgv_status,
            bgv_date=bgv_date,
            bgv_doc_url=bgv_doc_url,

            # ✅ Police Verification
            police_verification_status=police_verification_status,
            police_verification_date=police_verification_date,
            police_verification_doc_url=police_verification_doc_file_url,

            # ✅ Medical Verification
            medical_verification_status=medical_verification_status,
            medical_verification_date=medical_verification_date,
            medical_verification_doc_url=medical_verification_doc_file_url,

            # ✅ Training Verification
            training_verification_status=training_verification_status,
            training_verification_date=training_verification_date,
            training_verification_doc_url=training_verification_doc_file_url,

            # ✅ Eye Test
            eye_test_verification_status=eye_test_verification_status,
            eye_test_verification_date=eye_test_verification_date,
            eye_test_verification_doc_url=eye_test_verification_doc_file_url,

            # ✅ License
            license_number=license_number,
            license_expiry_date=license_expiry_date,
            license_doc_url=license_doc_file_url,


            # ✅ Induction
            induction_date=induction_date,
            induction_doc_url=induction_doc_file_url,

            # ✅ Badge
            badge_number=badge_number,
            badge_expiry_date=badge_expiry_date,
            badge_doc_url=badge_doc_file_url,

            # ✅ Alternate Govt ID
            alternate_govt_id=alternate_govt_id,
            alternate_govt_id_doc_type=alternate_govt_id_doc_type,
            alternate_govt_id_doc_url=alternate_govt_id_doc_file_url,
        )

        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)

        # Response
        return DriverOut.model_validate(new_driver, from_attributes=True)


    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {str(e.orig)}")
        raise HTTPException(status_code=400, detail="Integrity error while creating driver.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating driver.")
    except HTTPException as e:
        db.rollback()
        logger.warning(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        db.rollback()
        logger.exception("Unhandled error in driver creation: %s", str(e))
        traceback.print_exc()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while creating driver.")
    

@router.put("/{vendor_id}/drivers/{driver_id}", response_model=DriverOut, status_code=status.HTTP_200_OK)
async def update_driver(
    # form_data: DriverUpdate = Depends(),  # reuse schema, all fields should be Optional
    driver_id: int,
    vendor_id: int,
    name: Optional[str] = Form(...),
    email: Optional[EmailStr] = Form(...),
    hashed_password: Optional[str] = Form(...),
    mobile_number: Optional[str] = Form(...),

    city: Optional[str] = Form(...),
    date_of_birth: Optional[date] = Form(...),
    gender: Optional[str] = Form(...),

    alternate_mobile_number: Optional[str] = Form(...),
    permanent_address: Optional[str] = Form(...),
    current_address: Optional[str] = Form(...),

    bgv_status: Optional[str] = Form(...),
    bgv_date: Optional[date] = Form(...),

    police_verification_status: Optional[str] = Form(...),
    police_verification_date: Optional[date] = Form(...),

    medical_verification_status: Optional[str] = Form(...),
    medical_verification_date: Optional[date] = Form(...),

    training_verification_status: Optional[str] = Form(...),
    training_verification_date: Optional[date] = Form(...),

    eye_test_verification_status: Optional[str] = Form(...),
    eye_test_verification_date: Optional[date] = Form(...),

    license_number: Optional[str] = Form(...),
    license_expiry_date: Optional[date] = Form(...),

    induction_date: Optional[date] = Form(...),

    badge_number: Optional[str] = Form(...),
    badge_expiry_date: Optional[date] = Form(...),

    alternate_govt_id: Optional[str] = Form(...),
    alternate_govt_id_doc_type: Optional[str] = Form(...),

    bgv_doc_file: Optional[UploadFile] = None,
    police_verification_doc_file: Optional[UploadFile] = None,
    medical_verification_doc_file: Optional[UploadFile] = None,
    training_verification_doc_file: Optional[UploadFile] = None,
    eye_test_verification_doc_file: Optional[UploadFile] = None,
    license_doc_file: Optional[UploadFile] = None,
    induction_doc_file: Optional[UploadFile] = None,
    badge_doc_file: Optional[UploadFile] = None,
    alternate_govt_id_doc_file: Optional[UploadFile] = None,
    photo_image: Optional[UploadFile] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["driver_management.update"]))
):
    try:
        logger.info(f"[DRIVER_UPDATE] Attempting update: driver_id={driver_id}, vendor_id={vendor_id}")

        # ✅ Ensure driver belongs to this vendor
        driver = (
            db.query(Driver)
            .filter(Driver.driver_id == driver_id, Driver.vendor_id == vendor_id)
            .first()
        )

        if not driver:
            logger.warning(f"Driver ID {driver_id} not found for Vendor ID {vendor_id}")
            raise HTTPException(status_code=404, detail="Driver not found for this vendor")
        logger.info(f"[DRIVER_UPDATE] Attempt for driver_id={driver_id}")
        driver = db.query(Driver).filter_by(driver_id=driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found.")

        # Check for unique email
        if email and email != driver.email:
            existing_email = db.query(Driver).filter(Driver.email == email).first()
            if existing_email and existing_email.driver_id != driver.driver_id:
                raise HTTPException(status_code=409, detail="Email already exists.")

        # Check for unique mobile number
        if mobile_number and mobile_number != driver.mobile_number:
            existing_mobile = db.query(Driver).filter(Driver.mobile_number == mobile_number).first()
            if existing_mobile and existing_mobile.driver_id != driver.driver_id:
                raise HTTPException(status_code=409, detail="Mobile number already exists.")

        if hashed_password:
            driver.hashed_password = hash_password(hashed_password)

        # Validate and save each file (if provided)
        # Upload files
        async def process_file(doc_file, doc_type, allowed_types ,driver_code=None):
            if doc_file:
                validated = await file_size_validator(doc_file, allowed_types=allowed_types)
                return  save_file(doc_file, vendor_id, driver_code, doc_type)
            return None
        # bgv_doc_url = await process_file(bgv_doc_file, "bgv", ["application/pdf"])
        bgv_doc_url = await process_file(bgv_doc_file, "bgv", ["application/pdf"], driver.driver_code)
        if bgv_doc_url:
            logger.info(f"BGV document updated at: {bgv_doc_url}")
        police_verification_doc_file_url = await process_file(police_verification_doc_file, "police_verification", ["application/pdf"], driver.driver_code)
        if police_verification_doc_file_url:
            logger.info(f"Police verification document updated at: {police_verification_doc_file_url}")
        medical_verification_doc_file_url = await process_file(medical_verification_doc_file, "medical_verification", ["application/pdf"], driver.driver_code)
        if medical_verification_doc_file_url:
            logger.info(f"Medical verification document updated at: {medical_verification_doc_file_url}")
        training_verification_doc_file_url = await process_file(training_verification_doc_file, "training_verification", ["application/pdf"], driver.driver_code)
        if training_verification_doc_file_url:
            logger.info(f"Training verification document updated at: {training_verification_doc_file_url}")
        eye_test_verification_doc_file_url = await process_file(eye_test_verification_doc_file, "eye_test_verification", ["application/pdf"], driver.driver_code)
        if eye_test_verification_doc_file_url:
            logger.info(f"Eye test verification document updated at: {eye_test_verification_doc_file_url}")
        license_doc_file_url = await process_file(license_doc_file, "license", ["application/pdf"], driver.driver_code)
        if license_doc_file_url:
            logger.info(f"License document updated at: {license_doc_file_url}")
        induction_doc_file_url = await process_file(induction_doc_file, "induction", ["application/pdf"], driver.driver_code)
        if induction_doc_file_url:
            logger.info(f"Induction document updated at: {induction_doc_file_url}")
        badge_doc_file_url = await process_file(badge_doc_file, "badge", ["application/pdf"], driver.driver_code)
        if badge_doc_file_url:
            logger.info(f"Badge document updated at: {badge_doc_file_url}")
        alternate_govt_id_doc_file_url = await process_file(alternate_govt_id_doc_file, "alternate_govt_id", ["application/pdf"], driver.driver_code)
        if alternate_govt_id_doc_file_url:
            logger.info(f"Alternate government ID document updated at: {alternate_govt_id_doc_file_url}")
        photo_image_url = await process_file(photo_image, "photo", ["image/jpeg", "image/jpg", "image/png"], driver.driver_code)
        if photo_image_url:
            logger.info(f"Photo image updated at: {photo_image_url}")

        # Update fields only if provided
        update_fields = {
            "name": name,
            "email": email,
            "mobile_number": mobile_number,
            "hashed_password": hashed_password,
            "alternate_mobile_number": alternate_mobile_number,
            "city": city,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "permanent_address": permanent_address,
            "current_address": current_address,
            "bgv_status": bgv_status,
            "bgv_date": bgv_date,
            "police_verification_status": police_verification_status,
            "police_verification_date": police_verification_date,
            "medical_verification_status": medical_verification_status,
            "medical_verification_date": medical_verification_date,
            "training_verification_status": training_verification_status,
            "training_verification_date": training_verification_date,
            "eye_test_verification_status": eye_test_verification_status,
            "eye_test_verification_date": eye_test_verification_date,
            "license_number": license_number,
            "license_expiry_date": license_expiry_date,
            "induction_date": induction_date,
            "badge_number": badge_number,
            "badge_expiry_date": badge_expiry_date,
            "alternate_govt_id": alternate_govt_id,
            "alternate_govt_id_doc_type": alternate_govt_id_doc_type
        }

        # Set non-empty form fields
        for field, value in update_fields.items():
            if value is not None:
                setattr(driver, field, value)

        # Set uploaded file URLs
        if bgv_doc_url: driver.bgv_doc_url = bgv_doc_url
        if police_verification_doc_file_url: driver.police_verification_doc_url = police_verification_doc_file_url
        if medical_verification_doc_file_url: driver.medical_verification_doc_url = medical_verification_doc_file_url
        if training_verification_doc_file_url: driver.training_verification_doc_url = training_verification_doc_file_url
        if eye_test_verification_doc_file_url: driver.eye_test_verification_doc_url = eye_test_verification_doc_file_url
        if license_doc_file_url: driver.license_doc_url = license_doc_file_url
        if induction_doc_file_url: driver.induction_doc_url = induction_doc_file_url
        if badge_doc_file_url: driver.badge_doc_url = badge_doc_file_url
        if alternate_govt_id_doc_file_url: driver.alternate_govt_id_doc_url = alternate_govt_id_doc_file_url
        if photo_image_url: driver.photo_url = photo_image_url

        db.commit()
        db.refresh(driver)
        logger.info(f"Driver updated successfully: driver_id={driver.driver_id}, email={driver.email}")
        return DriverOut.model_validate(driver, from_attributes=True)

    except HTTPException as e:
        db.rollback()
        logger.warning(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        db.rollback()
        logger.exception("Unhandled exception in update_driver")
        raise HTTPException(status_code=500, detail="Unexpected error during driver update.")

@router.get("/{vendor_id}/drivers/", response_model=List[DriverOut])
def get_drivers_by_vendor(
    vendor_id: int,
    skip: int = 0,
    limit: int = 10,
    bgv_status: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by username or email"),
    driver_id: Optional[int] = None,
    driver_code: Optional[str] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["driver_management.create", "driver_management.read"]))
):
    try:
        logger.info(
            f"Fetching drivers for vendor_id={vendor_id} with filters: skip={skip}, "
            f"limit={limit}, bgv_status={bgv_status}, search={search}, "
            f"driver_id={driver_id}, driver_code={driver_code}"
        )

        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")

        query = db.query(Driver).filter(Driver.vendor_id == vendor_id)

        if driver_id:
            query = query.filter(Driver.driver_id == driver_id)

        if driver_code:
            query = query.filter(Driver.driver_code == driver_code)

        if bgv_status:
            query = query.filter(Driver.bgv_status == bgv_status)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Driver.driver_name.ilike(search_term),
                    Driver.email.ilike(search_term)
                )
            )

        drivers = query.offset(skip).limit(limit).all()
        

        if not drivers:
            logger.warning("No drivers found for given filters.")
            raise HTTPException(status_code=404, detail="No drivers found for the given filters.")

        return drivers
    except HTTPException as e:
        raise e  # Allow FastAPI to handle it properly (don't override with 500)
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching drivers.")
    except Exception as e:
        logger.exception("Unexpected error while fetching drivers.")
        raise HTTPException(status_code=500, detail="Unexpected error while fetching drivers.")
 
@router.patch("/{vendor_id}/drivers/{driver_id}/status", response_model=DriverOut)
def toggle_driver_status(
    vendor_id: int,
    driver_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["driver_management.update"]))
):
    try:
        driver = (
            db.query(Driver)
            .filter(Driver.driver_id == driver_id, Driver.vendor_id == vendor_id)
            .first()
        )

        if not driver:
            logger.warning(f"Driver ID {driver_id} not found for Vendor ID {vendor_id}")
            raise HTTPException(status_code=404, detail="Driver not found for this vendor")

        driver.is_active = not driver.is_active
        db.commit()
        db.refresh(driver)

        status = "activated" if driver.is_active else "deactivated"
        logger.info(f"Driver {driver_id} under vendor {vendor_id} successfully {status}")
        return driver

    except HTTPException as http_exc:
        raise http_exc  # Don't override HTTPExceptions (like 404)

    except Exception as e:
        logger.exception(f"Error toggling status: {str(e)}")  # Use exception() to log full stack
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("/{vendor_id}/drivers/{driver_id}/status", response_model=DriverOut)
def update_driver_status(
    vendor_id: int,
    driver_id: int,
    status: StatusUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["driver_management.update"]))
):
    try:
        driver = db.query(Driver).filter_by(driver_id=driver_id, vendor_id=vendor_id).first()
        if not driver:
            logger.warning(f"Driver ID {driver_id} not found for vendor ID {vendor_id}")
            raise HTTPException(status_code=404, detail="Driver not found for this vendor")

        if driver.is_active == status.is_active:
            current_state = "active" if status.is_active else "inactive"
            logger.info(f"Driver {driver_id} is already {current_state}")
            raise HTTPException(status_code=400, detail=f"Driver is already {current_state}")

        driver.is_active = status.is_active
        db.commit()
        db.refresh(driver)

        new_state = "activated" if driver.is_active else "deactivated"
        logger.info(f"Driver {driver_id} under vendor {vendor_id} successfully {new_state}")
        return driver

    except HTTPException as http_exc:
        raise http_exc  # Allow FastAPI to handle proper HTTPException responses
    
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error while toggling driver status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
