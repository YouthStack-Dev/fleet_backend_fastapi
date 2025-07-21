import traceback
from fastapi import APIRouter, Depends, status, Form, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import DriverCreate, DriverOut, DriverUpdate
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

logger = logging.getLogger(__name__)
router = APIRouter()


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
def save_file(file: Optional[UploadFile], driver_uuid: str, doc_type: str) -> Optional[str]:
    if file and file.filename:
        # Secure and unique filename
        import uuid
        safe_filename = f"{uuid.uuid4().hex}_{file.filename.replace(' ', '_')}"
        folder_path = os.path.join("uploaded_files", "drivers", str(driver_uuid), doc_type)
        os.makedirs(folder_path, exist_ok=True)

        # ✅ Construct full file path including the filename
        file_path = os.path.join(folder_path, safe_filename)

        # Save the file content to disk
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Get relative path for DB, and full path for logs
        rel_path = os.path.relpath(file_path, start="uploaded_files")
        abs_path = os.path.abspath(file_path)

        logger.info(f"{doc_type.upper()} document saved at: {abs_path}")
        return rel_path
    else:
        logger.debug(f"No file provided for {doc_type}")
    return None
@router.post("/", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
async def create_driver(
    vendor_id: int,
    form_data: DriverCreate = Depends(),
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
        logger.info(f"Creating driver for vendor_id={vendor_id} with email={form_data.email}")
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
        if not form_data.username.strip():
            raise HTTPException(status_code=422, detail="Username is required.")
        if not form_data.email.strip():
            raise HTTPException(status_code=422, detail="Email is required.")
        if '@' not in form_data.email:
            raise HTTPException(status_code=422, detail="Invalid email format.")
        if not form_data.mobile_number.strip():
            raise HTTPException(status_code=422, detail="Mobile number is required.")
        if len(form_data.mobile_number) > 15:
            raise HTTPException(status_code=422, detail="Mobile number too long.")
        if not form_data.hashed_password.strip():
            raise HTTPException(status_code=422, detail="Password is required.")

        # Vendor Check
        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")
        tenant_id = vendor.tenant_id

        # Reuse or create user
        # Check if user already exists for this tenant
        db_user = db.query(User).filter_by(email=form_data.email.strip(), tenant_id=vendor.tenant_id).first()

        if db_user:
            # Make sure the user is not already a driver
            existing_driver = db.query(Driver).filter_by(user_id=db_user.user_id).first()
            if existing_driver:
                raise HTTPException(status_code=409, detail="User already exists as a driver.")
        else:
            # Create new user
            new_user = User(
                username=form_data.username.strip(),
                email=form_data.email.strip(),
                mobile_number=form_data.mobile_number.strip(),
                hashed_password=hash_password(form_data.hashed_password.strip()),  # ✅ hashed
                tenant_id=vendor.tenant_id
            )
            db.add(new_user)
            db.flush()
            logger.info(f"User created successfully: {new_user.email}, id={new_user.user_id}")
            db_user = new_user


        # ✅ Safety check before using db_user
        if not db_user:
            logger.error("User creation failed or user not found.")
            raise HTTPException(status_code=500, detail="User creation failed.")

        # Now safe to use
        user_id = db_user.user_id

        # Save BGV Document



        driver_uuid = str(uuid4())
        bgv_doc_url = save_file(bgv_doc_file, driver_uuid, "bgv")
        if bgv_doc_url:
            logger.info(f"BGV document saved at: {bgv_doc_url}")
        police_verification_doc_file_url = save_file(police_verification_doc_file, driver_uuid, "police_verification")
        if police_verification_doc_file_url:
            logger.info(f"Police verification document saved at: {police_verification_doc_file_url}")
        medical_verification_doc_file_url = save_file(medical_verification_doc_file, driver_uuid, "medical_verification")
        if medical_verification_doc_file_url:
            logger.info(f"Medical verification document saved at: {medical_verification_doc_file_url}")
        training_verification_doc_file_url = save_file(training_verification_doc_file, driver_uuid, "training_verification")
        if training_verification_doc_file_url:
            logger.info(f"Training verification document saved at: {training_verification_doc_file_url}")
        eye_test_verification_doc_file_url = save_file(eye_test_verification_doc_file, driver_uuid, "eye_test_verification")
        if eye_test_verification_doc_file_url:
            logger.info(f"Eye test verification document saved at: {eye_test_verification_doc_file_url}")
        license_doc_file_url = save_file(license_doc_file, driver_uuid, "license")
        if license_doc_file_url:
            logger.info(f"License document saved at: {license_doc_file_url}")
        induction_doc_file_url = save_file(induction_doc_file, driver_uuid, "induction")
        if induction_doc_file_url:
            logger.info(f"Induction document saved at: {induction_doc_file_url}")
        badge_doc_file_url = save_file(badge_doc_file, driver_uuid, "badge")
        if badge_doc_file_url:
            logger.info(f"Badge document saved at: {badge_doc_file_url}")
        alternate_govt_id_doc_file_url = save_file(alternate_govt_id_doc_file, driver_uuid, "alternate_govt_id")
        if alternate_govt_id_doc_file_url:
            logger.info(f"Alternate government ID document saved at: {alternate_govt_id_doc_file_url}")
        photo_image_url = save_file(photo_image, driver_uuid, "photo")
        if photo_image_url:
            logger.info(f"Photo image saved at: {photo_image_url}")

        # Create Driver
        new_driver = Driver(
            user_id=db_user.user_id,
            vendor_id=vendor_id,
            alternate_mobile_number=form_data.alternate_mobile_number,
            city=form_data.city,
            date_of_birth=form_data.date_of_birth,
            gender=form_data.gender,
            permanent_address=form_data.permanent_address,
            current_address=form_data.current_address,
            photo_url=photo_image_url,

            # ✅ BGV
            bgv_status=form_data.bgv_status,
            bgv_date=form_data.bgv_date,
            bgv_doc_url=bgv_doc_url,

            # ✅ Police Verification
            police_verification_status=form_data.police_verification_status,
            police_verification_date=form_data.police_verification_date,
            police_verification_doc_url=police_verification_doc_file_url,

            # ✅ Medical Verification
            medical_verification_status=form_data.medical_verification_status,
            medical_verification_date=form_data.medical_verification_date,
            medical_verification_doc_url=medical_verification_doc_file_url,

            # ✅ Training Verification
            training_verification_status=form_data.training_verification_status,
            training_verification_date=form_data.training_verification_date,
            training_verification_doc_url=training_verification_doc_file_url,

            # ✅ Eye Test
            eye_test_verification_status=form_data.eye_test_verification_status,
            eye_test_verification_date=form_data.eye_test_verification_date,
            eye_test_verification_doc_url=eye_test_verification_doc_file_url,

            # ✅ License
            license_number=form_data.license_number,
            license_expiry_date=form_data.license_expiry_date,
            license_doc_url=license_doc_file_url,


            # ✅ Induction
            induction_date=form_data.induction_date,
            induction_doc_url=induction_doc_file_url,

            # ✅ Badge
            badge_number=form_data.badge_number,
            badge_expiry_date=form_data.badge_expiry_date,
            badge_doc_url=badge_doc_file_url,

            # ✅ Alternate Govt ID
            alternate_govt_id=form_data.alternate_govt_id,
            alternate_govt_id_doc_type=form_data.alternate_govt_id_doc_type,
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
    
from sqlalchemy import or_
from fastapi import Query
from typing import List, Optional

@router.put("/", response_model=DriverOut, status_code=status.HTTP_200_OK)
async def update_driver(
    user_id: int = Form(...),
    form_data: DriverUpdate = Depends(),  # reuse schema, all fields should be Optional
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
        logger.info(f"Updating driver with user_id={user_id}")
        driver = db.query(Driver).filter_by(user_id=user_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found.")

        driver_uuid = str(driver.driver_uuid)
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        # --- Update user fields if provided ---
        if form_data.username and form_data.username != user.username:
            existing_user = db.query(User).filter_by(username=form_data.username, tenant_id=user.tenant_id).first()
            if existing_user and existing_user.user_id != user.user_id:
                raise HTTPException(status_code=409, detail="Username already exists for this tenant.")
            user.username = form_data.username

        if form_data.email and form_data.email != user.email:
            existing_email = db.query(User).filter_by(email=form_data.email, tenant_id=user.tenant_id).first()
            if existing_email and existing_email.user_id != user.user_id:
                raise HTTPException(status_code=409, detail="Email already exists for this tenant.")
            user.email = form_data.email

        if form_data.mobile_number and form_data.mobile_number != user.mobile_number:
            existing_mobile = db.query(User).filter_by(mobile_number=form_data.mobile_number).first()
            if existing_mobile and existing_mobile.user_id != user.user_id:
                raise HTTPException(status_code=409, detail="Mobile number already exists.")
            user.mobile_number = form_data.mobile_number

        if form_data.hashed_password:
            user.hashed_password = hash_password(form_data.hashed_password)

        # Validate and save each file (if provided)
        async def process_file(doc_file, doc_type, allowed_types):
            if doc_file:
                validated = await file_size_validator(doc_file, allowed_types=allowed_types)
                return await save_file(validated, driver_uuid, doc_type)
            return None

        bgv_doc_url = await process_file(bgv_doc_file, "bgv", ["application/pdf"])
        if bgv_doc_url:
            logger.info(f"BGV document updated at: {bgv_doc_url}")
        police_verification_doc_file_url = await process_file(police_verification_doc_file, "police_verification", ["application/pdf"])
        if police_verification_doc_file_url:
            logger.info(f"Police verification document updated at: {police_verification_doc_file_url}")
        medical_verification_doc_file_url = await process_file(medical_verification_doc_file, "medical_verification", ["application/pdf"])
        if medical_verification_doc_file_url:
            logger.info(f"Medical verification document updated at: {medical_verification_doc_file_url}")
        training_verification_doc_file_url = await process_file(training_verification_doc_file, "training_verification", ["application/pdf"])
        if training_verification_doc_file_url:
            logger.info(f"Training verification document updated at: {training_verification_doc_file_url}")
        eye_test_verification_doc_file_url = await process_file(eye_test_verification_doc_file, "eye_test_verification", ["application/pdf"])
        if eye_test_verification_doc_file_url:
            logger.info(f"Eye test verification document updated at: {eye_test_verification_doc_file_url}")
        license_doc_file_url = await process_file(license_doc_file, "license", ["application/pdf"])
        if license_doc_file_url:
            logger.info(f"License document updated at: {license_doc_file_url}")
        induction_doc_file_url = await process_file(induction_doc_file, "induction", ["application/pdf"])
        if induction_doc_file_url:
            logger.info(f"Induction document updated at: {induction_doc_file_url}")
        badge_doc_file_url = await process_file(badge_doc_file, "badge", ["application/pdf"])
        if badge_doc_file_url:
            logger.info(f"Badge document updated at: {badge_doc_file_url}")
        alternate_govt_id_doc_file_url = await process_file(alternate_govt_id_doc_file, "alternate_govt_id", ["application/pdf"])
        if alternate_govt_id_doc_file_url:
            logger.info(f"Alternate government ID document updated at: {alternate_govt_id_doc_file_url}")
        photo_image_url = await process_file(photo_image, "photo", ["image/jpeg", "image/jpg", "image/png"])
        if photo_image_url:
            logger.info(f"Photo image updated at: {photo_image_url}")

        # Update fields only if provided
        update_fields = {
            "username": form_data.username,
            "email": form_data.email,
            "mobile_number": form_data.mobile_number,
            "hashed_password": form_data.hashed_password,
            "alternate_mobile_number": form_data.alternate_mobile_number,
            "city": form_data.city,
            "date_of_birth": form_data.date_of_birth,
            "gender": form_data.gender,
            "permanent_address": form_data.permanent_address,
            "current_address": form_data.current_address,
            "bgv_status": form_data.bgv_status,
            "bgv_date": form_data.bgv_date,
            "police_verification_status": form_data.police_verification_status,
            "police_verification_date": form_data.police_verification_date,
            "medical_verification_status": form_data.medical_verification_status,
            "medical_verification_date": form_data.medical_verification_date,
            "training_verification_status": form_data.training_verification_status,
            "training_verification_date": form_data.training_verification_date,
            "eye_test_verification_status": form_data.eye_test_verification_status,
            "eye_test_verification_date": form_data.eye_test_verification_date,
            "license_number": form_data.license_number,
            "license_expiry_date": form_data.license_expiry_date,
            "induction_date": form_data.induction_date,
            "badge_number": form_data.badge_number,
            "badge_expiry_date": form_data.badge_expiry_date,
            "alternate_govt_id": form_data.alternate_govt_id,
            "alternate_govt_id_doc_type": form_data.alternate_govt_id_doc_type
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
        logger.info(f"Driver updated successfully: user_id={user_id}")
        return DriverOut.model_validate(driver, from_attributes=True)

    except HTTPException as e:
        db.rollback()
        logger.warning(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        db.rollback()
        logger.exception("Unhandled exception in update_driver")
        raise HTTPException(status_code=500, detail="Unexpected error during driver update.")

@router.get("/", response_model=List[DriverOut])
def get_drivers_by_vendor(
    vendor_id: int,
    skip: int = 0,
    limit: int = 10,
    bgv_status: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by username or email"),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["driver_management.create", "driver_management.read"]))
):
    try:
        logger.info(f"Fetching drivers for vendor_id={vendor_id} with filters: skip={skip}, limit={limit}, bgv_status={bgv_status}, search={search}")

        vendor = db.query(Vendor).filter_by(vendor_id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")

        query = db.query(Driver).join(User).filter(Driver.vendor_id == vendor_id)

        if bgv_status:
            query = query.filter(Driver.bgv_status == bgv_status)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term)
            ))

        drivers = query.offset(skip).limit(limit).all()
        return drivers

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching drivers.")
    except Exception as e:
        logger.exception("Unexpected error while fetching drivers.")
        raise HTTPException(status_code=500, detail="Unexpected error while fetching drivers.")
