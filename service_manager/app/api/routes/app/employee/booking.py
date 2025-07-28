import logging
from app.database.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.schemas.schemas import ShiftResponse   
from app.api.routes.app.employee.auth import PermissionChecker
from app.database.models import Shift  # Adjust the import path as necessary
router = APIRouter(tags=["employee Booking"])
logger = logging.getLogger(__name__)

@router.post("/employee/common-shifts/")
def get_common_shifts_for_dates(
    dates: List[str] = Body(..., embed=True),
    log_type: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker([])),
):
    import datetime
    import calendar
    from app.database.models import Shift
    from fastapi.logger import logger

    try:
        tenant_id = token_data.get("tenant_id")
        if not tenant_id:
            logger.error("Tenant ID missing in token")
            raise HTTPException(status_code=400, detail="Tenant ID missing in token")

        # Validate log_type
        log_type = log_type.lower()
        if log_type not in ["in", "out"]:
            logger.error(f"Invalid log_type: {log_type}")
            raise HTTPException(status_code=400, detail="Invalid log_type. Use 'in' or 'out'.")

        # Check for duplicate dates
        if len(dates) != len(set(dates)):
            logger.warning(f"Duplicate dates provided: {dates}")
            raise HTTPException(status_code=400, detail="Dates contain duplicates.")

        today = datetime.date.today()
        days = set()

        for date_str in dates:
            try:
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"Invalid date format: {date_str}")
                raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD.")

            if date_obj < today:
                logger.warning(f"Past date provided: {date_str}")
                raise HTTPException(status_code=400, detail=f"Date {date_str} is in the past.")

            days.add(calendar.day_name[date_obj.weekday()].lower())

        # Query all shifts for tenant with given log_type
        shifts = (
            db.query(Shift)
            .filter(
                Shift.tenant_id == tenant_id,
                Shift.log_type == log_type
            )
            .all()
        )

        # Match shifts based on days
        matched_shifts = []
        for shift in shifts:
            if not shift.day:
                continue
            shift_days = shift.day.strip("{}").lower().replace(" ", "").split(",")
            if any(day in shift_days for day in days):
                matched_shifts.append(shift)

        response = {
            "your_dates": dates,
            "count": len(matched_shifts),
            "days_matched": list(days),
            "shifts": [
                {
                    "shift_id": shift.id,
                    "day": shift.day,
                    "log_type": shift.log_type,
                    "shift_time": shift.shift_time.strftime("%H:%M") if isinstance(shift.shift_time, datetime.time) else str(shift.shift_time),
                    "pickup_type": shift.pickup_type,
                    "gender": shift.gender
                }
                for shift in matched_shifts
            ]
        }

        logger.info(f"Returning {len(matched_shifts)} matched shifts for tenant_id={tenant_id}")
        return response
    except HTTPException as e:
        logger.error(f"HTTPException: {str(e.detail)}")
        raise e

    except Exception as exc:
        logger.exception("Error while fetching common shifts")
        raise HTTPException(status_code=500, detail="Something went wrong while processing shifts.")
