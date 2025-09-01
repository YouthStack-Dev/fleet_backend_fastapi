from uuid import uuid4

def build_response(data=None, message="Success", code=200, status="success"):
    return {
        "status": status,
        "code": code,
        "message": message,
        "meta": {"request_id": str(uuid4()), "timestamp": datetime.utcnow().isoformat()},
        "data": data if data is not None else None
    }
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

def handle_db_exception(e, request_id: str):
    if isinstance(e, IntegrityError):
        return {
            "status": "error",
            "code": 400,
            "message": "Database integrity error.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }           
    elif isinstance(e, SQLAlchemyError):
        return {
            "status": "error",
            "code": 500,
            "message": "Database error.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    elif isinstance(e, HTTPException):
        return {
            "status": "error",
            "code": e.status_code,
            "message": str(e.detail),
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }
    else:
        return {
            "status": "error",
            "code": 500,
            "message": "Unexpected error.",
            "meta": {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()},
            "data": {}
        }