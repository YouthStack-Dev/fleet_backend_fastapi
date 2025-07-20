import traceback
from fastapi import APIRouter, Depends, status, Form, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import DriverCreate, DriverOut
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


async def file_size_validator(file: Optional[UploadFile] = File(None), max_size_mb: int = 200) -> Optional[UploadFile]:

    logger.info(f"Setting file size validator with max size: {max_size_mb}MB")
    # async def validate() -> Optional[UploadFile]:

    if file is None:
        return None  # file is optional
    logger.info(f"Validating file: {file.filename}") 

    contents = await file.read()
    file.file = io.BytesIO(contents)  # reset stream for downstream usage

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"{file.filename} is too large. Max size allowed is {max_size_mb}MB.",
        )
    return file
    # return validate
import asyncio

def sync_wrapper(file: Optional[UploadFile] = File(None)) -> Optional[UploadFile]:
    logger.info(f"Sync wrapper called for file: {file.filename if file else 'None'}")

    result = asyncio.run(file_size_validator(file))
    logger.info("No file provided, returning None")

    return result

MAX_SIZE_MB = 5  # change as needed

@router.post("/", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(
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
