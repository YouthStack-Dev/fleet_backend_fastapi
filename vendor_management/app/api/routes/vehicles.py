from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db

router = APIRouter()



@router.post("/create/")
def add_vehicle():
    """Endpoint to create a new vehicle."""
    pass
@router.get("/get/{vehicle_id}")
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    pass

@router.get("/get_all/")
def get_all_vehicles(db: Session = Depends(get_db)):
    pass

@router.delete("/delete/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    pass

@router.put("/update/{vehicle_id}")
def update_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    pass

@router.delete("/bulk_delete/")
def bulk_delete_vehicle(vehicle_ids: list[int], db: Session = Depends(get_db)):
    pass

@router.get("/search/")
def search_vehicles(query: str, db: Session = Depends(get_db)):
    pass

@router.get("/count/")
def count_vehicles(db: Session = Depends(get_db)):
    pass

@router.post("/bulk_create/")
def bulk_create_vehicles(db: Session = Depends(get_db)):
    pass
    