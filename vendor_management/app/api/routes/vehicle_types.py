from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db

router = APIRouter()



@router.post("/create/")
def add_vehicle_type():
    """Endpoint to create a new vehicle type."""
    pass
@router.get("/get/{vehicle_type_id}")
def get_vehicle_type(vehicle_type_id: int, db: Session = Depends(get_db)):
    pass

@router.get("/get_all/")
def get_all_vehicle_types(db: Session = Depends(get_db)):
    pass

@router.delete("/delete/{vehicle_type_id}")
def delete_vehicle_type(vehicle_type_id: int, db: Session = Depends(get_db)):
    pass

@router.put("/update/{vehicle_type_id}")
def update_vehicle_type(vehicle_type_id: int, db: Session = Depends(get_db)):
    pass

@router.delete("/bulk_delete/")
def bulk_delete_vehicle_type(vehicle_type_ids: list[int], db: Session = Depends(get_db)):
    pass

@router.get("/search/")
def search_vehicle_types(query: str, db: Session = Depends(get_db)):
    pass

@router.get("/count/")
def count_vehicle_types(db: Session = Depends(get_db)):
    pass

@router.post("/bulk_create/")
def bulk_create_vehicle_types(db: Session = Depends(get_db)):
    pass
    