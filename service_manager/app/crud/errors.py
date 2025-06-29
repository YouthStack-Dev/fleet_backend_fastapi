from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    DataError,
    DatabaseError,
    ProgrammingError,
    OperationalError
)

from fastapi import HTTPException
from typing import Optional, Dict, Any
from datetime import datetime

class DatabaseException(Exception):
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    
def handle_integrity_error( error: IntegrityError) -> Exception:
    error_msg = str(error.orig)
    if "unique constraint" in error_msg.lower():
        if "users_email_key" in error_msg:
            raise HTTPException(
                detail="Email already exists",
                status_code=409,
            )
        elif "users_username_key" in error_msg:
            raise HTTPException(
                detail="Username already exists",
                status_code=409,
            )
    elif "foreign key constraint" in error_msg.lower():
        if "tenant_id" in error_msg:
            raise HTTPException(
                detail="Invalid tenant ID",
                status_code=409,
            )
    raise HTTPException(
        detail="Database integrity error",
        status_code=400
    )