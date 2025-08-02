from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import logging
from app.api.schemas.schemas import ShiftBookingResponse , BookingOut
from sqlalchemy.orm import joinedload
from app.database.models import Booking, Shift
from common_utils.auth.permission_checker import PermissionChecker
from app.database.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/shift-bookings/", response_model=ShiftBookingResponse)
def get_shift_bookings(
    shift_id: int = Body(..., embed=True),
    token_data: dict = Depends(PermissionChecker(["cutoff.create"])),
    db: Session = Depends(get_db),
):
    tenant_id = token_data.get("tenant_id")
    logger.info(f"Fetching bookings for shift_id={shift_id}, tenant_id={tenant_id}")

    shift = db.query(Shift).filter(Shift.id == shift_id, Shift.tenant_id == tenant_id).first()
    if not shift:
        logger.warning(f"Shift not found: shift_id={shift_id}, tenant_id={tenant_id}")
        raise HTTPException(status_code=404, detail="Shift not found for this tenant")

    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.employee))
        .filter(Booking.shift_id == shift_id)
        .all()
    )

    result = [
        BookingOut(
            booking_id=b.booking_id,
            employee_id=b.employee_id,
            employee_code=b.employee_code,
            employee_name = b.employee.name if b.employee else None,
            pickup_location=b.pickup_location,
            pickup_location_latitude=b.pickup_location_latitude,
            pickup_location_longitude=b.pickup_location_longitude,
            drop_location=b.drop_location,
            drop_location_latitude=b.drop_location_latitude,
            drop_location_longitude=b.drop_location_longitude,
            status=b.status,
        )
        for b in bookings
    ]

    return ShiftBookingResponse(shift_id=shift_id, bookings=result)
