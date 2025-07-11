# app/controller/driver_controller.py

from app.crud.crud import create_driver

class DriverController:
    def create_driver(self, db, driver, tenant_id):
        return create_driver(db, driver, tenant_id)
