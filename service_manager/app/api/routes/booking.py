import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import logging
from app.api.schemas.schemas import ConfirmRouteRequest, PickupDetail, RouteSuggestion, RouteSuggestionData, RouteSuggestionRequest,  GenerateRouteRequest, RouteSuggestionResponse,GenerateRouteResponse,TempRoute,PickupPoint, ShiftBookingResponse , BookingOut, ShiftInfo
from sqlalchemy.orm import joinedload
from app.database.models import Booking, Shift, ShiftRoute
from common_utils.auth.permission_checker import PermissionChecker
from app.database.database import get_db
router = APIRouter(tags=["Admin Bookings"])
logger = logging.getLogger(__name__)
import traceback
import requests
import os
# GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # Set this in your .env
GOOGLE_MAPS_API_KEY = "AIzaSyCI7CwlYJ6Qt5pQGW--inSsJmdEManW-K0"  

@router.post("/routes/generate", response_model=GenerateRouteResponse)
def generate_shift_routes(payload: GenerateRouteRequest, db: Session = Depends(get_db)):
    shift_id = payload.shift_id
    try:
        logger.info(f"Generating route for shift_id: {shift_id}")

        # Step 1: Fetch bookings
        bookings = db.query(Booking).filter(Booking.shift_id == shift_id).all()
        if not bookings:
            logger.warning(f"No bookings found for shift_id: {shift_id}")
            raise HTTPException(status_code=404, detail="No bookings found for this shift")
        
        # Get tenant office location from shift -> tenant
        shift = db.query(Shift).filter(Shift.id == shift_id).first()
        if not shift or not shift.tenant:
            logger.error("Shift or tenant not found for shift_id: %s", shift_id)
            raise HTTPException(status_code=404, detail="Shift or Tenant not found")

        tenant = shift.tenant
        try:
            DROP_LAT = float(tenant.latitude)
            DROP_LNG = float(tenant.longitude)
        except (TypeError, ValueError):
            logger.error("Invalid latitude or longitude in tenant config")
            raise HTTPException(status_code=500, detail="Invalid tenant location data")

        DROP_ADDRESS = tenant.address or "Office"


        # Step 2: Group bookings in chunks of 3
        def chunk(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        booking_groups = list(chunk(bookings, 3))
        routes = []

        for idx, group in enumerate(booking_groups, start=1):
            origin = f"{group[0].pickup_location_latitude},{group[0].pickup_location_longitude}"
            waypoints = "|".join([f"{b.pickup_location_latitude},{b.pickup_location_longitude}" for b in group[1:]])
            logger.info(f"Processing group {idx} with origin: {origin} and waypoints: {waypoints}")
            print(f"Origin: {origin}, Destination: {DROP_LAT},{DROP_LNG}, Waypoints: {waypoints}")

            url = f"https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": origin,
                "destination": f"{DROP_LAT},{DROP_LNG}",
                "waypoints": f"optimize:true|{waypoints}" if waypoints else "",
                "key": GOOGLE_MAPS_API_KEY
            }

            logger.info(f"Requesting Google Maps directions API with params: {params}")
            response = requests.get(url, params=params)

            if response.status_code != 200:
                logger.error(f"Google Maps API request failed: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to fetch directions from Google Maps API")

            data = response.json()
            if not data.get("routes"):
                logger.warning("Google Maps API returned no routes")
                raise HTTPException(status_code=400, detail="No route returned from Google Maps")

            route = data["routes"][0]
            order = route.get("waypoint_order", [])
            leg_data = route.get("legs", [])

            distance = sum(leg["distance"]["value"] for leg in leg_data) / 1000  # km
            duration = sum(leg["duration"]["value"] for leg in leg_data) / 60    # minutes

            ordered = [group[0]] + [group[1:][i] for i in order] if waypoints else group

            pickup_order = [
                PickupPoint(
                    booking_id=b.booking_id,
                    pickup_lat=b.pickup_location_latitude,
                    pickup_lng=b.pickup_location_longitude
                )
                for b in ordered
            ]

            routes.append(
                TempRoute(
                    temp_route_id=idx,
                    booking_ids=[b.booking_id for b in ordered],
                    pickup_order=pickup_order,
                    estimated_time=f"{int(duration)} mins",
                    estimated_distance=f"{round(distance, 1)} km",
                    drop_lat=DROP_LAT,
                    drop_lng=DROP_LNG,
                    drop_address=DROP_ADDRESS
                )
            )


        logger.info(f"Generated {len(routes)} routes for shift_id: {shift_id}")
        return GenerateRouteResponse(shift_id=shift_id, routes=routes)

    except Exception as e:
        logger.exception("Error generating shift routes")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error generating shift routes")
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import date, datetime
import logging

from app.database.models import Shift, Booking
from app.api.schemas.schemas import ShiftsByDateResponse, BookingOut
from common_utils.auth.permission_checker import PermissionChecker
from app.database.database import get_db

logger = logging.getLogger(__name__)

@router.get("/admin/shift-bookings/")
def get_shift_bookings_by_date(
    date: str = Query(..., description="Date to filter bookings, format: YYYY-MM-DD"),
    token_data: dict = Depends(PermissionChecker(["cutoff.create"])),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to fetch all shifts with bookings for a specific date.
    Returns response in a standardized structured envelope with meta data.
    """
    request_id = str(uuid.uuid4())
    tenant_id = token_data.get("tenant_id")
    logger.info(f"[{request_id}] Fetching bookings for tenant_id={tenant_id} on date={date}")

    try:
        # Validate date format
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"[{request_id}] Invalid date format: {date}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Fetch all shifts for this tenant
        shifts = db.query(Shift).filter(Shift.tenant_id == tenant_id).all()
        if not shifts:
            logger.warning(f"[{request_id}] No shifts configured for tenant_id={tenant_id}")
            raise HTTPException(status_code=404, detail="No shifts configured for this tenant")

        # Initialize data
        shifts_data = []
        total_bookings = 0

        # Loop over shifts and count bookings directly
        for shift in shifts:
            booking_count = (
                db.query(Booking)
                .filter(
                    Booking.tenant_id == tenant_id,
                    Booking.shift_id == shift.id,
                    Booking.booking_date == filter_date
                )
                .count()
            )

            if booking_count > 0:
                total_bookings += booking_count
                shifts_data.append({
                    "shift_id": shift.id,
                    "shift_code": shift.shift_code,
                    "log_type": shift.log_type,
                    "shift_time": shift.shift_time,
                    "day": shift.day,
                    "pickup_type": shift.pickup_type,
                    "gender": shift.gender,
                    "date": date,
                    "total_bookings": booking_count
                })

        if total_bookings == 0:
            logger.info(f"[{request_id}] No bookings found for tenant_id={tenant_id} on date={date}")
            return {
                "status": "success",
                "code": 200,
                "message": "No bookings done for any shifts on the specified date",
                "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
                "data": {"date": date, "shifts": []}
            }

        return {
            "status": "success",
            "code": 200,
            "message": f"Shift booking counts fetched for {date}",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {"date": date, "shifts": shifts_data}
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"[{request_id}] IntegrityError: {str(e.orig)}")
        return {
            "status": "error",
            "code": 400,
            "message": "Database integrity error while fetching shift bookings.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[{request_id}] SQLAlchemyError: {str(e)}")
        return {
            "status": "error",
            "code": 500,
            "message": "Database error while fetching shift bookings.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    except HTTPException as e:
        logger.warning(f"[{request_id}] HTTPException: {str(e.detail)}")
        return {
            "status": "error",
            "code": e.status_code,
            "message": str(e.detail),
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}")
        return {
            "status": "error",
            "code": 500,
            "message": "Unexpected error while fetching shift bookings.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }


@router.get("/admin/shift-booking-details/")
def get_shift_booking_details(
    shift_id: int = Query(..., description="ID of the shift"),
    date: str = Query(..., description="Date to filter bookings, format: YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of bookings per page"),
    token_data: dict = Depends(PermissionChecker(["cutoff.create"])),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to fetch bookings for a specific shift and date with pagination.
    Returns structured response with metadata.
    """
    request_id = str(uuid.uuid4())
    tenant_id = token_data.get("tenant_id")
    logger.info(f"[{request_id}] Fetching bookings for tenant_id={tenant_id}, shift_id={shift_id}, date={date}")

    try:
        # Validate date format
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"[{request_id}] Invalid date format: {date}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Fetch shift and verify it belongs to tenant
        shift = db.query(Shift).filter(Shift.id == shift_id, Shift.tenant_id == tenant_id).first()
        if not shift:
            logger.warning(f"[{request_id}] Shift not found for tenant_id={tenant_id}, shift_id={shift_id}")
            raise HTTPException(status_code=404, detail="Shift not found for this tenant")

        # Base query for bookings
        bookings_query = (
            db.query(Booking)
            .options(joinedload(Booking.employee))
            .filter(
                Booking.shift_id == shift_id,
                Booking.booking_date == filter_date
            )
        )

        total_bookings_count = bookings_query.count()

        if total_bookings_count == 0:
            logger.info(f"[{request_id}] No bookings found for shift_id={shift_id} on date={date}")
            raise HTTPException(status_code=200, detail="No bookings found for this shift on the selected date")

        # Apply pagination
        bookings = bookings_query.offset((page - 1) * limit).limit(limit).all()

        # Prepare bookings data
        booking_list = [
            BookingOut(
                booking_id=b.booking_id,
                employee_id=b.employee_id,
                employee_code=b.employee_code,
                employee_name=b.employee.name if b.employee else None,
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

        logger.info(f"[{request_id}] Fetched {len(bookings)} bookings "
                    f"(page={page}, limit={limit}) for shift_id={shift_id} on date={date}")

        # Success response
        return {
            "status": "success",
            "code": 200,
            "message": f"Shift bookings fetched for shift_id={shift_id} on {date}",
            "meta": {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_records": total_bookings_count,
                    "total_pages": (total_bookings_count + limit - 1) // limit
                }
            },
            "data": {
                "shift_id": shift.id,
                "shift_code": shift.shift_code,
                "date": date,
                "total_bookings": total_bookings_count,
                "bookings": booking_list
            }
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"[{request_id}] IntegrityError: {str(e.orig)}")
        return {
            "status": "error",
            "code": 400,
            "message": "Database integrity error while fetching shift booking details.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[{request_id}] SQLAlchemyError: {str(e)}")
        return {
            "status": "error",
            "code": 500,
            "message": "Database error while fetching shift booking details.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    except HTTPException as e:
        logger.warning(f"[{request_id}] HTTPException: {e.detail}")
        return {
            "status": "error",
            "code": e.status_code,
            "message": str(e.detail),
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}")
        return {
            "status": "error",
            "code": 500,
            "message": "Unexpected error while fetching shift booking details.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }


@router.post("/admin/routes/suggest", response_model=RouteSuggestionResponse)
def suggest_routes(
    payload: RouteSuggestionRequest,
    token_data: dict = Depends(PermissionChecker(["cutoff.create"])),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to suggest optimized routes for a shift on a specific date.
    Does not assign drivers — generates a draft arrangement only.
    """
    request_id = str(uuid.uuid4())
    tenant_id = token_data.get("tenant_id")
    logger.info(f"[{request_id}] Generating draft route suggestion for tenant_id={tenant_id}, shift_id={payload.shift_id}, date={payload.date}")

    try:
        # Validate date format
        try:
            filter_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        if filter_date < date.today():
            raise HTTPException(status_code=400, detail="Date cannot be in the past")
        # Fetch shift & tenant
        shift = db.query(Shift).filter(
            Shift.id == payload.shift_id,
            Shift.tenant_id == tenant_id
        ).first()
        if not shift or not shift.tenant:
            raise HTTPException(status_code=404, detail="Shift or tenant not found")

        tenant = shift.tenant
        try:
            DROP_LAT = float(tenant.latitude)
            DROP_LNG = float(tenant.longitude)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid tenant location data")

        # Fetch bookings
        bookings = db.query(Booking).filter(
            Booking.shift_id == payload.shift_id,
            Booking.booking_date == filter_date
        ).all()
        if not bookings:
            raise HTTPException(status_code=404, detail="No bookings found for this shift and date")

        # Chunk bookings
        def chunk(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        booking_groups = list(chunk(bookings, 3))
        suggested_routes = []

        # Google Maps API per group
        for idx, group in enumerate(booking_groups, start=1):
            origin = f"{group[0].pickup_location_latitude},{group[0].pickup_location_longitude}"
            waypoints = "|".join(
                f"{b.pickup_location_latitude},{b.pickup_location_longitude}" for b in group[1:]
            )

            params = {
                "origin": origin,
                "destination": f"{DROP_LAT},{DROP_LNG}",
                "waypoints": f"optimize:true|{waypoints}" if waypoints else "",
                "key": GOOGLE_MAPS_API_KEY
            }
            response = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=params)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch route from Google Maps")

            data = response.json()
            if not data.get("routes"):
                logger.warning(f"[{request_id}] No route found for group {idx}")
                continue

            route_data = data["routes"][0]
            order = route_data.get("waypoint_order", [])
            legs = route_data.get("legs", [])

            total_distance_km = sum(l["distance"]["value"] for l in legs) / 1000
            total_duration_min = sum(l["duration"]["value"] for l in legs) / 60

            ordered_bookings = [group[0]] + [group[1:][i] for i in order] if waypoints else group

            suggested_routes.append(
                RouteSuggestion(
                    route_number=idx,
                    booking_ids=[str(b.booking_id) for b in ordered_bookings],
                    pickups=[
                        PickupDetail(
                            booking_id=str(b.booking_id),
                            employee_name=b.employee.name if b.employee else None,
                            latitude=b.pickup_location_latitude,
                            longitude=b.pickup_location_longitude,
                            address=b.pickup_location,
                            landmark=b.employee.landmark if b.employee else None
                        )
                        for b in ordered_bookings
                    ],
                    estimated_distance_km=round(total_distance_km, 2),
                    estimated_duration_min=int(total_duration_min),
                    drop_lat=DROP_LAT,
                    drop_lng=DROP_LNG,
                    drop_address=tenant.address or "Office"
                )
            )

        return RouteSuggestionResponse(
            status="success",
            code=200,
            message=f"Draft route suggestions generated for {payload.date}",
            meta={"request_id": request_id, "generated_at": datetime.utcnow().isoformat()},
            data=RouteSuggestionData(
                shift_id=shift.id,
                shift_code=shift.shift_code,
                date=payload.date,
                total_routes=len(suggested_routes),
                routes=suggested_routes
            )
        )

    except HTTPException as e:
        db.rollback()
        logger.warning(f"[{request_id}] HTTPException: {e.detail}")
        return RouteSuggestionResponse(
            status="error",
            code=e.status_code,
            message=str(e.detail),
            meta={"request_id": request_id, "generated_at": datetime.utcnow().isoformat()},
            data=None
        )

    except IntegrityError as e:
        db.rollback()
        logger.error(f"[{request_id}] IntegrityError: {str(e.orig)}")
        return RouteSuggestionResponse(
            status="error",
            code=400,
            message="Database integrity error.",
            meta={"request_id": request_id, "generated_at": datetime.utcnow().isoformat()},
            data=None
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[{request_id}] SQLAlchemyError: {str(e)}")
        return RouteSuggestionResponse(
            status="error",
            code=500,
            message="Database error.",
            meta={"request_id": request_id, "generated_at": datetime.utcnow().isoformat()},
            data=None
        )

    except Exception as e:
        db.rollback()
        logger.error(f"[{request_id}] Unexpected error: {str(e)}")
        return RouteSuggestionResponse(
            status="error",
            code=500,
            message="Unexpected error while generating route suggestions.",
            meta={"request_id": request_id, "generated_at": datetime.utcnow().isoformat()},
            data=None
        )
# @router.post("/admin/routes/confirm")
# async def confirm_routes_debug(request: Request):
#     raw = await request.body()
#     print("RAW BODY:", raw)

@router.post("/admin/routes/confirm", response_model=RouteSuggestionResponse)
def confirm_routes(
    payload: ConfirmRouteRequest,
    token_data: dict = Depends(PermissionChecker(["cutoff.create"])),
    db: Session = Depends(get_db)
):

    request_id = str(uuid.uuid4())
    tenant_id = token_data.get("tenant_id")
    logger.info(f"[{request_id}] Confirming routes for shift_id={payload.shift_id}, date={payload.date}")

    try:
        # Validate date
        filter_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        if filter_date < date.today():
            raise HTTPException(status_code=400, detail="Date cannot be in the past")

        # Fetch shift
        shift = db.query(Shift).filter(
            Shift.id == payload.shift_id,
            Shift.tenant_id == tenant_id
        ).first()
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")

        # Optional: validate each booking exists
        all_booking_ids = [b.booking_id for r in payload.routes for b in r.pickups]
        bookings = db.query(Booking).filter(
            Booking.booking_id.in_(all_booking_ids),
            Booking.shift_id == payload.shift_id,
            Booking.booking_date == filter_date
        ).all()
        if len(bookings) != len(all_booking_ids):
            raise HTTPException(status_code=400, detail="Some bookings do not exist for this shift/date")

        # Save routes
        for route in payload.routes:
            route_entry = ShiftRoute(
                shift_id=payload.shift_id,
                route_date=filter_date,
                route_number=route.route_number,
                route_data=jsonable_encoder(route),
                confirmed=payload.confirmed
            )
            db.add(route_entry)
        db.commit()

        return RouteSuggestionResponse(
            status="success",
            code=200,
            message="Routes confirmed successfully" if payload.confirmed else "Routes saved as draft",
            meta={"request_id": request_id, "generated_at": datetime.utcnow().isoformat()},
            data=None
        )

    except HTTPException as e:
        db.rollback()
        logger.warning(f"[{request_id}] HTTPException: {e.detail}")
        return RouteSuggestionResponse(
            status="error",
            code=e.status_code,
            message=str(e.detail),
            meta={"request_id": request_id, "generated_at": datetime.utcnow().isoformat()},
            data=None
        )

    except Exception as e:
        db.rollback()
        logger.error(f"[{request_id}] Unexpected error: {str(e)}")
        return RouteSuggestionResponse(
            status="error",
            code=500,
            message="Unexpected error while confirming routes",
            meta={"request_id": request_id, "generated_at": datetime.utcnow().isoformat()},
            data=None
        )
