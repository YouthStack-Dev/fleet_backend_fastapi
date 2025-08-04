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

router = APIRouter(tags=["Bookings"])
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




import traceback
import logging
import requests
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.schemas.schemas import (
    GenerateRouteRequest,
    GenerateRouteResponse,
    TempRoute,
    PickupPoint
)
import os
logger = logging.getLogger(__name__)
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
