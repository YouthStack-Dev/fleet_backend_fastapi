from typing import Union
from fastapi import FastAPI
from app.api.routes.tenants import router as tenant_router
from app.api.routes.services import router as service_router
from app.api.routes.groups import router as group_router
from app.api.routes.policies import router as policy_router
from app.api.routes.users import router as user_router
from app.api.routes.mappings import router as mappings_router
from app.api.routes.auth import router as auth_router
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


app.include_router(tenant_router, prefix="/api/tenants", tags=["tenants"])
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