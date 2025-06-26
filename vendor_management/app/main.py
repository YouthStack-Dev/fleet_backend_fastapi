from typing import Union
from fastapi import FastAPI
# from app.api.routes.vehicles import router as group_router
# from app.api.routes.vehicle_types import router as user_router
# from app.api.routes.drivers import router as tenant_router
# from app.api.routes.contract import router as mappings_router

from contextlib import asynccontextmanager
from app.database.database import init_db, seed_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create models
    init_db()
    
    # seed_data()
    yield


app = FastAPI(title="Service Manager", lifespan=lifespan)
# app = FastAPI(title="Service Manager")


# app.include_router(tenant_router, prefix="/api/drivers", tags=["drivers"])
# app.include_router(group_router, prefix="/api/vehicles", tags=["vehicles"])
# app.include_router(user_router, prefix="/api/vehicle_types", tags=["vehicle_types"])
# app.include_router(mappings_router, prefix="/api/contract", tags=["contract"])

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}