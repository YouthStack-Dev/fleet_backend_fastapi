from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db

router = APIRouter()



@router.post("/create/")
def add_driver():
    """Endpoint to create a new driver."""
    pass
@router.get("/get/{driver_id}")
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    pass

@router.get("/get_all/")
def get_all_drivers(db: Session = Depends(get_db)):
    pass

@router.delete("/delete/{driver_id}")
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    pass

@router.put("/update/{driver_id}")
def update_driver(driver_id: int, db: Session = Depends(get_db)):
    pass

@router.delete("/bulk_delete/")
def bulk_delete_driver(driver_ids: list[int], db: Session = Depends(get_db)):
    pass

@router.get("/search/")
def search_drivers(query: str, db: Session = Depends(get_db)):
    pass

@router.get("/count/")
def count_drivers(db: Session = Depends(get_db)):
    pass

@router.post("/bulk_create/")
def bulk_create_drivers( db: Session = Depends(get_db)):
    pass
    