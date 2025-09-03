import json
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
load_dotenv()  # It will load .env file values into os.environ
# Add this import at the top of main.py
from starlette.status import HTTP_415_UNSUPPORTED_MEDIA_TYPE

from typing import Union
from fastapi import FastAPI
from app.api.routes.tenants import router as tenant_router
from app.api.routes.services import router as service_router
from app.api.routes.groups import router as group_router
from app.api.routes.policies import router as policy_router
from app.api.routes.users import router as user_router
from app.api.routes.mappings import router as mappings_router
from app.api.routes.auth import router as auth_router
from app.api.routes.department import router as department_router
from app.api.routes.employee import router as employee_router
from app.api.routes.cutoff import router as cutoff_router
from app.api.routes.shift import router as shift_router
from app.api.routes.vendor import router as vendor_router
from app.api.routes.vehicle_type import router as vehicle_type_router
from app.api.routes.driver import router as driver_router
from app.api.routes.vehicle import router as vehicle_router
from app.api.routes.app.employee.auth import router as app_auth_router
from app.api.routes.app.employee.booking import router as employee_booking_router
from app.api.routes.booking import router as booking_router
from contextlib import asynccontextmanager
from app.database.database import init_db, seed_iam, seed_data
from fastapi.middleware.cors import CORSMiddleware
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create models
    init_db()
    
    # seed_iam()
    seed_data()
    yield


app = FastAPI(title="Service Manager", lifespan=lifespan)
# app = FastAPI(title="Service Manager")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://euronext.gocab.tech",
        "https://api.gocab.tech",
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:5174",
        "http://localhost:8100",
        "http://api.gocab.tech",
    ],
    allow_credentials=True,
    # allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_methods=["*"],
    # allow_headers=["Authorization", "Content-Type"],
    allow_headers=["*"],
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"[REQUEST] {request.method} {request.url}")
        logger.info(f"[HEADERS] Content-Type: {request.headers.get('content-type')}")
        response = await call_next(request)
        return response
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Safely decode request body
    body = None
    if isinstance(exc.body, (bytes, bytearray)):
        try:
            body = exc.body.decode("utf-8")
        except Exception:
            body = str(exc.body)
    else:
        body = exc.body

    # Build structured log
    log_data = {
        "type": "validation_error",
        "method": request.method,
        "url": str(request.url),
        "query_params": dict(request.query_params),
        "body": body,
        "errors": exc.errors()
    }

    # Log as JSON string (so it’s easy for ELK/Splunk/Sentry to parse)
    logger.error(json.dumps(log_data, default=str))

    # Return standard response
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Request validation failed"
        }
    )

import os
from fastapi.staticfiles import StaticFiles
# Local path inside container
UPLOAD_DIR = "/app/app/uploaded_files"

# Mount only if the folder exists
if os.path.exists(UPLOAD_DIR) and os.path.isdir(UPLOAD_DIR):
    logger.info(f"Mounting static files from {UPLOAD_DIR}")
    app.mount("/uploaded_files", StaticFiles(directory=UPLOAD_DIR), name="uploaded_files")
    logger.info(f"Mounted static files from {UPLOAD_DIR}")
else:
    logger.warning(f"Upload directory {UPLOAD_DIR} does not exist or is not a directory. Static files will not be served.")

app.add_middleware(RequestLoggerMiddleware)
app.include_router(app_auth_router, prefix="/api")
app.include_router(booking_router, prefix="/api")
app.include_router(employee_booking_router, prefix="/api")
app.include_router(vehicle_router, prefix="/api/vendors", tags=["vehicles"])
app.include_router(driver_router, prefix="/api/vendors", tags=["drivers"])
app.include_router(vehicle_type_router, prefix="/api/vehicle_types", tags=["vehicle_types"])
app.include_router(tenant_router, prefix="/api/tenants", tags=["tenants"])
app.include_router(vendor_router, prefix="/api/vendors", tags=["vendors"])
app.include_router(shift_router, prefix="/api/shifts", tags=["shifts"])
app.include_router(cutoff_router, prefix="/api/cutoff", tags=["cutoff"])
app.include_router(employee_router, prefix="/api/employees", tags=["employees"])
app.include_router(department_router, prefix="/api/departments", tags=["departments"])
app.include_router(service_router, prefix="/api/services", tags=["services"])
app.include_router(group_router, prefix="/api/groups", tags=["groups"])
app.include_router(policy_router, prefix="/api/policies", tags=["policies"])
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(mappings_router, prefix="/api/mappings", tags=["mappings"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}