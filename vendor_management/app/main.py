from typing import Union
from fastapi import FastAPI
from app.api.routes.contract import router as contract_router
from app.api.routes.vendor import router as vendor_router
from app.api.routes.drivers import router as drivers_router   
from app.api.routes.vehicles import router as vehicles_router
from app.api.routes.vehicle_types import router as vehicle_types_router
from contextlib import asynccontextmanager
from app.database.database import init_db, seed_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create models
    init_db()
    
    # seed_data()
    yield


app = FastAPI(title="vendor management", lifespan=lifespan)
# app = FastAPI(title="Service Manager")

app.include_router(contract_router, prefix="/api/contract", tags=["contract"])
app.include_router(vendor_router, prefix="/api/vendor", tags=["vendor"])
app.include_router(drivers_router, prefix="/api/drivers", tags=["drivers"])
app.include_router(vehicles_router, prefix="/api/vehicles", tags=["vehicles"])
app.include_router(vehicle_types_router, prefix="/api/vehicle_types", tags=["vehicle_types"])

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}