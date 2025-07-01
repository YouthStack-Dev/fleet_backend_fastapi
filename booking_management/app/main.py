from typing import Union
from fastapi import FastAPI
from app.api.routes.bookings import router as bookings_router
from app.api.routes.routes import router as route_router
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


app.include_router(bookings_router, prefix="/api/bookings", tags=["bookings"])
app.include_router(route_router, prefix="/api/routes", tags=["routes"])


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}