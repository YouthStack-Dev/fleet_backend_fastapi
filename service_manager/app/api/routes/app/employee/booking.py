import datetime
import logging

from anyio import current_time
from app.database.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.models import Booking, Employee, Tenant # Add additional imports
from app.api.schemas.schemas import ShiftResponse   
from app.api.routes.app.employee.auth import PermissionChecker
from app.database.models import Shift
router = APIRouter(tags=["employee Booking"])
logger = logging.getLogger(__name__)
@router.post("/employee/create_booking/")
def create_booking(
    token_data: dict = Depends(PermissionChecker([])),
    dates: str = Body(..., embed=True),
    shift_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    try:
        logger.info("Starting booking process.")
        # Validate token data
        tenant_id = token_data.get("tenant_id")
        employee_id = token_data.get("employee_id")
        logger.info(f"Tenant ID: {tenant_id}, Employee ID: {employee_id}")
        if not (tenant_id and employee_id):
            raise HTTPException(status_code=400, detail="Invalid token data")

        # Split and validate dates
        date_list = dates.split(",")
        booking_dates = []
        logger.info(f"Parsed booking dates: {booking_dates}")
        for date_str in date_list:
            try:
                booking_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                booking_dates.append(booking_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD.")

        # Check for duplicate dates
        if len(set(booking_dates)) != len(booking_dates):
            raise HTTPException(status_code=400, detail="Duplicate dates are not allowed.")

        # Fetch the shift
        shift = db.query(Shift).filter(Shift.id == shift_id, Shift.tenant_id == tenant_id).first()
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")

        logger.info("Fetching tenant details.")
        tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Fetch cutoff time for booking
        cutoff_time = db.query(tenant.cutoff.booking_cutoff).scalar()
        current_time = datetime.datetime.now().time()
        # Fetch employee details
        logger.info("Fetching employee details.")
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Determine pickup and drop-off locations
        if shift.log_type == "in":
            pickup_location = employee.address
            pickup_location_latitude = employee.latitude
            pickup_location_longitude = employee.longitude
            drop_location = tenant.address
            drop_latitude = tenant.latitude
            drop_longitude = tenant.longitude
        elif shift.log_type == "out":
            pickup_location = tenant.address
            pickup_location_latitude = tenant.latitude
            pickup_location_longitude = tenant.longitude
            drop_location = employee.address
            drop_latitude = employee.latitude
            drop_longitude = employee.longitude
        else:
            raise HTTPException(status_code=400, detail="Invalid shift type")

        # Validate existing bookings and cutoff
        logger.info("Validating existing bookings and cutoff times.")
        for booking_date in booking_dates:
            if booking_date <= datetime.datetime.now().date() and current_time >= datetime.time(cutoff_time):
                raise HTTPException(status_code=400, detail=f"Unable to book for {booking_date}, cutoff time exceeded.")
                # Check if booking dates match the shift's days
        valid_days = [day.strip().lower() for day in shift.day.split(",")]
        for booking_date in booking_dates:
            weekday = booking_date.strftime('%A').lower()
            if weekday not in valid_days:
                raise HTTPException(status_code=400, detail=f"Booking date {booking_date} does not match shift days {shift.day}.")


            existing_booking = db.query(Booking).filter(
                Booking.employee_id == employee_id,
                Booking.shift_id == shift_id,
                Booking.booking_date == booking_date
            ).first()

            if existing_booking and existing_booking.status != "Cancelled":
                raise HTTPException(status_code=400, detail=f"Existing booking for {booking_date}, not cancelled.")

            # Determine pickup and drop-off locations
            if shift.log_type == "in":
                pickup_location = employee.address
                pickup_location_latitude = employee.latitude
                pickup_location_longitude = employee.longitude
                drop_location = tenant.address
                drop_latitude = tenant.latitude
                drop_longitude = tenant.longitude
            elif shift.log_type == "out":
                pickup_location = tenant.address
                pickup_location_latitude = tenant.latitude
                pickup_location_longitude = tenant.longitude
                drop_location = employee.address
                drop_latitude = employee.latitude
                drop_longitude = employee.longitude
            else:
                raise HTTPException(status_code=400, detail="Invalid shift type")

            # Create booking
            booking = Booking(
                employee_id=employee_id,
                employee_code=employee.employee_code,
                tenant_id=tenant_id,
                shift_id=shift_id,
                department_id=employee.department_id,
                pickup_location=pickup_location,
                pickup_location_latitude=pickup_location_latitude,
                pickup_location_longitude=pickup_location_longitude,
                drop_location=drop_location,
                drop_location_latitude=drop_latitude,
                drop_location_longitude=drop_longitude,
                booking_date=booking_date,
                status="Pending",
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )

            db.add(booking)

        logger.info("Committing booking to the database.")
        db.commit()
        logger.info("Bookings created successfully for provided dates.")
        return {"detail": "Bookings created for all provided dates successfully"}
    
    except HTTPException as e:
        raise e  # This re-raises caught HTTPExceptions

    except Exception as exc:
        logger.exception("Unexpected error occurred during booking.")
        raise HTTPException(status_code=500, detail="An error occurred while creating the booking.")
    


@router.get("/employee/bookings/")
def get_all_bookings(
    token_data: dict = Depends(PermissionChecker([])),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info("Fetching all bookings for tenant.")
    try:
        # Validate token data
        tenant_id = token_data.get("tenant_id")
        if not tenant_id:
            logger.error("Tenant ID missing in token data.")
            raise HTTPException(status_code=400, detail="Invalid token data")
        logger.info(f"Tenant ID: {tenant_id}")

        # Fetch all bookings for the tenant
        query = db.query(Booking).filter(Booking.tenant_id == tenant_id)

        if status:
            logger.info(f"Filtering by status: {status}")
            query = query.filter(Booking.status == status)

        bookings = query.offset(skip).limit(limit).all()
        if not bookings:
            logger.info("No bookings found.")
            return {"detail": "No bookings found"}
        logger.info(f"Found {len(bookings)} bookings.")

        # Format booking data
        booking_list = []
        for booking in bookings:
            shift = db.query(Shift).filter(Shift.id == booking.shift_id).first()
            booking_list.append({
                "booking_id": booking.booking_id,
                "employee_id": booking.employee_id,
                "employee_code": booking.employee_code,
                "shift_details": {
                    "shift_id": shift.id,
                    "shift_code": shift.shift_code,
                    "log_type": shift.log_type,
                    "shift_time": shift.shift_time.strftime("%H:%M") if isinstance(shift.shift_time, datetime.time) else str(shift.shift_time),
                    "day": shift.day,
                    "pickup_type": shift.pickup_type,
                    "gender": shift.gender
                },
                "pickup_location": booking.pickup_location,
                "pickup_location_latitude": booking.pickup_location_latitude,
                "pickup_location_longitude": booking.pickup_location_longitude,
                "drop_location": booking.drop_location,
                "drop_location_latitude": booking.drop_location_latitude,
                "drop_location_longitude": booking.drop_location_longitude,
                "status": booking.status,
                "created_at": booking.created_at,
                "updated_at": booking.updated_at,
            })

        logger.info(f"Returning {len(booking_list)} bookings.")
        return {"bookings": booking_list}

    except HTTPException as e:
        raise e
    except Exception as exc:
        logger.exception("Error while fetching bookings.")
        raise HTTPException(status_code=500, detail="An error occurred while fetching bookings.")

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
