from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db

router = APIRouter()



@router.post("/create/")
def add_vendor():
    """Endpoint to create a new vendor."""
    pass
@router.get("/get/{vendor_id}")
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    pass

@router.get("/get_all/")
def get_all_vendors(db: Session = Depends(get_db)):
    pass

@router.delete("/delete/{vendor_id}")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    pass

@router.put("/update/{vendor_id}")
def update_vendor(vendor_id: int, db: Session = Depends(get_db)):
    pass

@router.delete("/bulk_delete/")
def bulk_delete_vendor(vendor_ids: list[int], db: Session = Depends(get_db)):
    pass

@router.get("/search/")
def search_vendors(query: str, db: Session = Depends(get_db)):
    pass

@router.get("/count/")
def count_vendors(db: Session = Depends(get_db)):
    pass

@router.post("/bulk_create/")
def bulk_create_vendors(db: Session = Depends(get_db)):
    pass
    