# app/api/routes/vendor_router.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.controller.vendor_controller import VendorController
from app.database.database import get_db
from app.api.schemas.schemas import VendorCreate, VendorOut, VendorUpdate
from common_utils.auth.permission_checker import PermissionChecker

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter()
controller = VendorController()


@router.post("/", response_model=VendorOut)
async def create_vendor(
    vendor_data: VendorCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vendor_management.create"]))
):
    tenant_id = token_data["tenant_id"]
    user_id = token_data["user_id"]

    logger.info(f"[CREATE] Request to create vendor: {vendor_data.vendor_name} for tenant_id: {tenant_id}")

    try:
        result = controller.create_vendor(db, tenant_id, user_id, vendor_data)
        logger.info(f"[CREATE] Vendor created successfully with ID: {result.vendor_id}")
        return result
    except HTTPException as e:
        logger.warning(f"[CREATE] HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("[CREATE] Unexpected error while creating vendor")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/", response_model=List[VendorOut])
async def get_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vendor_management.read"]))
):
    tenant_id = token_data["tenant_id"]
    logger.info(f"[READ] Fetching vendors for tenant_id={tenant_id}, skip={skip}, limit={limit}, is_active={is_active}")

    try:
        vendors = controller.get_vendors(db, tenant_id, skip, limit, is_active)
        logger.info(f"[READ] Retrieved {len(vendors)} vendors for tenant_id={tenant_id}")
        return vendors
    except HTTPException as http_ex:
        logger.warning(f"[READ] HTTPException: {http_ex.detail}")
        raise http_ex
    except Exception as ex:
        logger.exception("[READ] Unexpected error while fetching vendors")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{vendor_id}", response_model=VendorOut)
async def get_vendor_by_id(
    vendor_id: int = Path(..., gt=0, description="Vendor ID"),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vendor_management.read"]))
):
    tenant_id = token_data["tenant_id"]
    logger.info(f"[DETAIL] Fetching vendor_id: {vendor_id} for tenant_id: {tenant_id}")

    try:
        result = controller.get_vendor_by_id(db, tenant_id, vendor_id)
        logger.info(f"[DETAIL] Vendor found: {result.vendor_name} (ID: {result.vendor_id})")
        return result
    except HTTPException as e:
        logger.warning(f"[DETAIL] HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("[DETAIL] Unexpected error while fetching vendor by ID")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("/{vendor_id}", response_model=VendorOut)
async def update_vendor(
    vendor_id: int = Path(..., gt=0, description="Vendor ID"),
    update_data: VendorUpdate = ...,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vendor_management.update"]))
):
    tenant_id = token_data["tenant_id"]
    user_id = token_data["user_id"]
    logger.info(f"[UPDATE] Updating vendor_id: {vendor_id} for tenant_id: {tenant_id}")
    try:
        result = controller.update_vendor(db, tenant_id, vendor_id, update_data, user_id)
        logger.info(f"[UPDATE] Vendor updated successfully: {result.vendor_id}")
        return result
    except HTTPException as e:
        logger.warning(f"[UPDATE] HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("[UPDATE] Unexpected error while updating vendor")
        raise HTTPException(status_code=500, detail="Internal Server Error")
@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: int = Path(..., gt=0, description="Vendor ID"),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["vendor_management.delete"]))
):
    tenant_id = token_data["tenant_id"]
    user_id = token_data["user_id"]

    try:
        return controller.delete_vendor(db, tenant_id, vendor_id, user_id)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")