from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db  # Adjust the import based on your structure

router = APIRouter()


@router.post("/create/")
def add_booking():
    """Endpoint to create a new booking."""
    pass


@router.get("/get/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Endpoint to fetch a booking by ID."""
    pass


@router.get("/get_all/")
def get_all_bookings(db: Session = Depends(get_db)):
    """Endpoint to fetch all bookings."""
    pass


@router.delete("/delete/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    """Endpoint to delete a booking by ID."""
    pass


@router.put("/update/{booking_id}")
def update_booking(booking_id: int, db: Session = Depends(get_db)):
    """Endpoint to update a booking by ID."""
    pass
