# app/controller/driver_controller.py

from app.crud.crud import create_driver

class DriverController:
    def create_driver(self, db, driver, vendor_id):
        return create_driver(db, driver, vendor_id)
