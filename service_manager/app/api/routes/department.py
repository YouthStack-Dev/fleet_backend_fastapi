from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.database.models import Department
from app.api.schemas.schemas import DepartmentCreate, DepartmentOut, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(Department).filter_by(
        department_name=department.department_name,
        tenant_id=department.tenant_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Department with same name already exists for this tenant.")
    
    new_department = Department(**department.dict())
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    return new_department


@router.get("/", response_model=List[DepartmentOut])
def list_departments(tenant_id: int, db: Session = Depends(get_db)):
    return db.query(Department).filter_by(tenant_id=tenant_id).all()


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(department_id: int, db: Session = Depends(get_db)):
    department = db.query(Department).filter_by(department_id=department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")
    return department


@router.put("/{department_id}", response_model=DepartmentOut)
def update_department(department_id: int, department: DepartmentUpdate, db: Session = Depends(get_db)):
    db_department = db.query(Department).filter_by(department_id=department_id).first()
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found.")
    
    for key, value in department.dict(exclude_unset=True).items():
        setattr(db_department, key, value)
    
    db.commit()
    db.refresh(db_department)
    return db_department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: int, db: Session = Depends(get_db)):
    department = db.query(Department).filter_by(department_id=department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")
    
    db.delete(department)
    db.commit()
