from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db

router = APIRouter()



@router.post("/create/")
def add_slab():
    """Endpoint to create a new slab."""
    pass
@router.get("/get/{slab_id}")
def get_slab(slab_id: int, db: Session = Depends(get_db)):
    pass

@router.get("/get_all/")
def get_all_slabs(db: Session = Depends(get_db)):
    pass

@router.delete("/delete/{slab_id}")
def delete_slab(slab_id: int, db: Session = Depends(get_db)):
    pass

@router.put("/update/{slab_id}")
def update_slab(slab_id: int, db: Session = Depends(get_db)):
    pass

