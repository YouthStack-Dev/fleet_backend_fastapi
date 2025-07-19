from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.crud.crud import create_driver
from app.api.schemas.schemas import DriverCreate, DriverOut
import logging

logger = logging.getLogger(__name__)


def create_driver_controller(db: Session, driver: DriverCreate, vendor_id: int) -> DriverOut:
    try:
        logger.info(f"Creating driver for vendor_id={vendor_id}, email={driver.email}")
        created_driver = create_driver(db=db, driver=driver, vendor_id=vendor_id)
        return created_driver
    except HTTPException as e:
        logger.error(f"HTTPException during driver creation: {e.detail}")
        raise
    except Exception as e:
        logger.exception("Unexpected error during driver creation")
        raise HTTPException(status_code=500, detail="Internal Server Error")
