# app/utils/decorators.py
from functools import wraps
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.utils.response import build_response, handle_db_exception
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

from functools import wraps
import asyncio

def handle_exceptions(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        request_id = str(uuid4())
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except IntegrityError as e:
            db = kwargs.get("db")
            if db:
                db.rollback()
            logger.error(f"[{request_id}] IntegrityError: {str(e.orig)}")
            return build_response(message="Database integrity error", code=400, status="error")
        except SQLAlchemyError as e:
            db = kwargs.get("db")
            if db:
                db.rollback()
            logger.error(f"[{request_id}] SQLAlchemyError: {str(e)}")
            return build_response(message="Database error", code=500, status="error")
        except HTTPException as e:
            logger.warning(f"[{request_id}] HTTPException: {str(e.detail)}")
            return build_response(message=str(e.detail), code=e.status_code, status="error")
        except Exception as e:
            db = kwargs.get("db")
            if db:
                db.rollback()
            logger.exception(f"[{request_id}] Unexpected error: {str(e)}")
            return build_response(message="Unexpected error", code=500, status="error")
    return async_wrapper
