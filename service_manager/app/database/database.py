from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json
from sqlalchemy import Column, DateTime, func
from sqlalchemy.exc import IntegrityError



SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL","postgresql://servicemgr_user:password@localhost:5433/servicemgr_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    print("Creating tables")
    import app.database.models  # Ensure models are imported to create tables

    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized and tables created.")

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e
    


def seed_data():
    session = SessionLocal()
    try:
        from app.database.models import Tenant, User, Group, Role, Service, Module, Policy, user_tenant, group_user, group_role, user_role, Department, Employee , Cutoff , Shift , Vendor

        # Check if data already exists
        if session.query(Tenant).first():
            print("Data already exists, skipping seed")
            return

        # Create Tenants
        tenants = [
            Tenant(tenant_name="neru network", address="123 Main St, Anytown, USA", longitude="123.456", latitude="78.910", tenant_metadata={"industry": "Technology", "size": "Enterprise"}),
        ]
        
        for tenant in tenants:
            try:
                session.add(tenant)
                session.flush()
            except IntegrityError:
                session.rollback()
                tenant = session.query(Tenant).filter_by(tenant_name=tenant.tenant_name).first()
                if not tenant:
                    raise ValueError("Failed to create tenant")

        try:
            # Create Services
            services = [
                Service(name="Fleet Manager", description="Vehicle fleet management service", 
                       service_metadata={"version": "1.0", "api_key": "fleet123"}),
                Service(name="Booking System", description="Vehicle booking and scheduling", 
                       service_metadata={"version": "2.1", "api_key": "book456"}),
                Service(name="Analytics", description="Fleet analytics and reporting", 
                       service_metadata={"version": "1.2", "api_key": "analy789"})
            ]
            session.add_all(services)
            session.flush()

            # Create Modules
            modules = [
                Module(service_id=services[0].id, name="user_management", description="Manage user accounts"),  #0
                Module(service_id=services[0].id, name="department_management", description="Manage departments"), #1
                Module(service_id=services[0].id, name="employee_management", description="Manage employees"), #2
                Module(service_id=services[0].id, name="group_management", description="Manage user groups"), #3
                Module(service_id=services[0].id, name="mapping_management", description="Manage mappings between users, groups, and roles"), #4
                Module(service_id=services[0].id, name="policy_management", description="Manage policies"), #5
                Module(service_id=services[0].id, name="service_management", description="Manage services"), #6
                Module(service_id=services[0].id, name="tenant_management", description="Manage tenants"), #7
                Module(service_id=services[0].id, name="driver_management", description="Manage drivers"), #8
                Module(service_id=services[0].id, name="vehicle_management", description="Manage vehicles"), #9
                Module(service_id=services[0].id, name="vehicle_type_management", description="Manage vehicle types"), #10
                Module(service_id=services[0].id, name="vendor_management", description="Manage vendors"), #11
                Module(service_id=services[0].id, name="admin_dashboard", description="View system dashboards"), #12
                Module(service_id=services[0].id, name="company_dashboard", description="View company dashboards"), #13
                Module(service_id=services[0].id, name="routing_management", description="Manage routing operations"), #14
                Module(service_id=services[0].id, name="tracking_management", description="Manage tracking operations"), #15
                Module(service_id=services[0].id, name="booking_management", description="Manage bookings"), #16
                Module(service_id=services[0].id, name="shift_management", description="Manage shift operations"), #17
                # Module(service_id=services[0].id, name="manage_shift", description="Manage individual shift schedules"),
                Module(service_id=services[0].id, name="shift_category", description="Manage shift categories"), #18
                Module(service_id=services[0].id, name="cutoff", description="Manage cutoff times for bookings and cancellations"), #19

            ]
            session.add_all(modules)
            session.flush()

            # Create Users with different roles  password is dp for all users
            users = [
                User(username="admin", email="admin@gmail.com", hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d", 
                     tenant_id=tenants[0].tenant_id, is_active=1,
                     mobile_number="9876543210"),
                User(username="manager", email="manager@gmail.com", hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d", 
                     tenant_id=tenants[0].tenant_id, is_active=1,
                     mobile_number="9876543211"),
                User(username="driver", email="driver@gmail.com", hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d", 
                     tenant_id=tenants[0].tenant_id, is_active=1,
                     mobile_number="9876543212")
            ]
            session.add_all(users)
            session.flush()



            # Create Departments
            departments = [
                Department(tenant_id=tenants[0].tenant_id, department_name="IT", description="Technology department"),
                Department(tenant_id=tenants[0].tenant_id, department_name="Operations", description="Operations department"),
                Department(tenant_id=tenants[0].tenant_id, department_name="Medical", description="Medical staff department")
            ]
            session.add_all(departments)
            session.flush()

            # Create Employees (Assuming you want to make existing users employees)
            employees = [
                Employee(
                    name="Alice Johnson",
                    email="alice.johnson@example.com",
                    mobile_number="9123456789",
                    hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d",
                    employee_code="acm1",
                    tenant_id=tenants[0].tenant_id,
                    department_id=departments[0].department_id,
                    gender="Female",
                    alternate_mobile_number="9123456789",
                    office="Head Office",
                    special_need=None,
                    special_need_start_date=None,
                    special_need_end_date=None,
                    subscribe_via_email=True,
                    subscribe_via_sms=False,
                    address="Acme HQ, Tech Park",
                    latitude="12.9716",
                    longitude="77.5946",
                    landmark="Near Big Mall"
                ),
                Employee(
                    name="Bob Smith",
                    email="bob.smith@example.com",
                    mobile_number="9123456788",
                    hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d",
                    employee_code="sta1",
                    tenant_id=tenants[0].tenant_id,
                    department_id=departments[1].department_id,
                    gender="Male",
                    alternate_mobile_number=None,
                    office="Main Office",
                    special_need="Wheelchair Access",
                    special_need_start_date=None,
                    special_need_end_date=None,
                    subscribe_via_email=True,
                    subscribe_via_sms=True,
                    address="Startup Inc, Downtown",
                    latitude="28.7041",
                    longitude="77.1025",
                    landmark="Opposite Metro Station"
                ),
                Employee(
                    name="Charlie Medson",
                    email="charlie.medson@example.com",
                    mobile_number="9123456787",
                    hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d",
                    employee_code="med1",
                    tenant_id=tenants[0].tenant_id,
                    department_id=departments[2].department_id,
                    gender="Male",
                    alternate_mobile_number=None,
                    office="Med Solutions Office",
                    special_need=None,
                    special_need_start_date=None,
                    special_need_end_date=None,
                    subscribe_via_email=False,
                    subscribe_via_sms=True,
                    address="Med Solutions, Health Street",
                    latitude="19.0760",
                    longitude="72.8777",
                    landmark="Near City Hospital"
                )
            ]

            session.add_all(employees)
            session.flush()

        

            # Create Groups
            groups = [
                Group(group_name="Administrators", tenant_id=tenants[0].tenant_id, 
                     description="System administrators"),
                Group(group_name="Company Managers", tenant_id=tenants[0].tenant_id, 
                     description="Company managers"),
                Group(group_name="Drivers", tenant_id=tenants[0].tenant_id, 
                     description="Vehicle operators")
            ]
            session.add_all(groups)
            session.flush()

            # Create Roles
            roles = [
                Role(role_name="Super Admin", description="Full system access", tenant_id=tenants[0].tenant_id),
                Role(role_name="Fleet Manager", description="Fleet management access", tenant_id=tenants[0].tenant_id),
                Role(role_name="Driver", description="Vehicle operator access", tenant_id=tenants[0].tenant_id)
            ]
            session.add_all(roles)
            session.flush()

            # Create Policies
            policies = [
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[0].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[1].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[2].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[3].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[4].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[5].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[6].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[7].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[8].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[9].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[10].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[11].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[12].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[13].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[14].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[15].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[16].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[17].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[18].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[0].id, module_id=modules[19].id,
                      can_view=True, can_create=True, can_edit=True, can_delete=True,
                      group_id=groups[0].group_id, condition={"ip_range": "10.0.0.0/8"}),

            
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[1].id, module_id=modules[1].id,
                    can_view=True, can_create=True, can_edit=False, can_delete=False,
                    group_id=groups[1].group_id, condition={"ip_range": "10.0.0.0/8"}),
                Policy(tenant_id=tenants[0].tenant_id, service_id=services[1].id, module_id=modules[2].id,
                    can_view=True, can_create=True, can_edit=False, can_delete=False,
                    group_id=groups[1].group_id, condition={"ip_range": "10.0.0.0/8"}),

                Policy(tenant_id=tenants[0].tenant_id, service_id=services[1].id, module_id=modules[13].id,
                    can_view=True, can_create=True, can_edit=False, can_delete=False,
                    group_id=groups[1].group_id, condition={"ip_range": "10.0.0.0/8"}),

                Policy(tenant_id=tenants[0].tenant_id, service_id=services[1].id, module_id=modules[15].id,
                    can_view=True, can_create=True, can_edit=False, can_delete=False,
                    group_id=groups[1].group_id, condition={"ip_range": "10.0.0.0/8"}),


            ]
            session.add_all(policies)
            session.flush()

            # Create Mappings
            # User-Tenant mappings
            # User-Tenant mappings
            for user in users:
                session.execute(user_tenant.insert().values(
                    user_id=user.user_id,
                    tenant_id=tenants[0].tenant_id,
                    metadata={"role": "primary"}
                ))

            # Group-User mappings
            session.execute(group_user.insert().values(group_id=groups[0].group_id, user_id=users[0].user_id))  # admin -> Administrators
            session.execute(group_user.insert().values(group_id=groups[1].group_id, user_id=users[1].user_id))  # manager -> Fleet Managers
            session.execute(group_user.insert().values(group_id=groups[2].group_id, user_id=users[2].user_id))  # driver -> Drivers


            # Group-Role mappings
            session.execute(group_role.insert().values(group_id=groups[0].group_id, role_id=roles[0].role_id))  # Admin group -> Super Admin
            session.execute(group_role.insert().values(group_id=groups[1].group_id, role_id=roles[1].role_id))  # Fleet group -> Fleet Manager
            session.execute(group_role.insert().values(group_id=groups[2].group_id, role_id=roles[2].role_id))  # Drivers group -> Driver


            # User-Role mappings
            session.execute(user_role.insert().values(user_id=users[0].user_id, role_id=roles[0].role_id, tenant_id=tenants[0].tenant_id))  # admin
            session.execute(user_role.insert().values(user_id=users[1].user_id, role_id=roles[1].role_id, tenant_id=tenants[0].tenant_id))  # manager
            session.execute(user_role.insert().values(user_id=users[2].user_id, role_id=roles[2].role_id, tenant_id=tenants[0].tenant_id))  # driver


            cutoff = Cutoff(
                tenant_id=tenant.tenant_id,
                booking_cutoff=6,  # or your custom value
                cancellation_cutoff=6
            )
            session.add(cutoff)
            session.flush()
            from datetime import time
            from app.database.models import LogType, DayOfWeek, PickupType, GenderType

            shifts = [
                Shift(
                    tenant_id=tenant.tenant_id,
                    shift_code="MORNING_IN",
                    log_type=LogType.IN,
                    shift_time=time(9, 0),
                    day="{monday,wednesday,friday}",
                    waiting_time_minutes=10,
                    pickup_type=PickupType.PICKUP,
                    gender=GenderType.ANY,
                    is_active=True
                ),
                Shift(
                    tenant_id=tenant.tenant_id,
                    shift_code="EVENING_OUT",
                    log_type=LogType.OUT,
                    shift_time=time(18, 0),
                    day="{monday,wednesday}",
                    waiting_time_minutes=5,
                    pickup_type=PickupType.NODAL,
                    gender=GenderType.ANY,
                    is_active=True
                )
            ]
            session.add_all(shifts)
            session.flush()
            vendors = [
                Vendor(
                    tenant_id=tenants[0].tenant_id,
                    vendor_name="ABC Transport",
                    contact_person="John Doe",
                    phone_number="9876543210",
                    email="abc@example.com",
                    address="123, MG Road, Bengaluru",
                    is_active=True
                ),
                Vendor(
                    tenant_id=tenants[0].tenant_id,
                    vendor_name="SpeedLogistics",
                    contact_person="Priya Sharma",
                    phone_number="9876543211",
                    email="priya@speedlogistics.com",
                    address="45, Silk Board, Bengaluru",
                    is_active=True
                )
            ]
            session.add_all(vendors)
            session.flush()
            from app.database.models import VehicleType, FuelType, Driver, Vehicle, Device

            vehicle_types = [
                VehicleType(
                    name="Swift Dzire",
                    description="Compact sedan for city rides",
                    capacity=4,
                    fuel_type=FuelType.PETROL,
                    vendor_id=vendors[0].vendor_id,
                ),
                VehicleType(
                    name="Eeco Cargo",
                    description="Cargo van for delivery",
                    capacity=2,
                    fuel_type=FuelType.CNG,
                    vendor_id=vendors[0].vendor_id,
                ),
                VehicleType(
                    name="Innova Crysta",
                    description="Spacious MPV for long trips",
                    capacity=6,
                    fuel_type=FuelType.DIESEL,
                    vendor_id=vendors[0].vendor_id,
                ),
                VehicleType(
                    name="Tata Nexon EV",
                    description="Electric SUV for local travel",
                    capacity=5,
                    fuel_type=FuelType.ELECTRIC,
                    vendor_id=vendors[1].vendor_id,
                ),
            ]
            session.add_all(vehicle_types)
            session.flush()

            drivers = [
                Driver(
                    driver_code="MLT001",
                    name="John Doe",
                    email="john.doe@example.com",
                    mobile_number="9876543210",
                    hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d",
                    vendor_id=vendors[0].vendor_id,
                    gender="Male",
                    bgv_doc_url="https://example.com/docs/john_bgv.pdf"
                ),
                Driver(
                    driver_code="MLT002",
                    name="Alice Smith",
                    email="alice.smith@example.com",
                    mobile_number="9876543211",
                    hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d",
                    vendor_id=vendors[0].vendor_id,
                    gender="Female",
                    bgv_doc_url="https://example.com/docs/alice_bgv.pdf"
                ),
                Driver(
                    driver_code="MLT003",
                    name="Bob Johnson",
                    email="bob.johnson@example.com",
                    mobile_number="9876543212",
                    hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d",
                    vendor_id=vendors[1].vendor_id,
                    gender="Male",
                    bgv_doc_url="https://example.com/docs/bob_bgv.pdf"
                ),
            ]
            session.add_all(drivers)
            session.flush()
                # --- Seed Vehicles ---
            vehicles = [
                Vehicle(
                    vendor_id=vendors[0].vendor_id,
                    vehicle_type_id=vehicle_types[0].vehicle_type_id,
                    driver_id=drivers[0].driver_id,
                    vehicle_code="veh001",
                    reg_number="KA01AB1234",
                    status="ACTIVE",
                    rc_card_url="https://example.com/rc/veh001.pdf"
                ),
                Vehicle(
                    vendor_id=vendors[0].vendor_id,
                    vehicle_type_id=vehicle_types[1].vehicle_type_id,
                    driver_id=drivers[1].driver_id,
                    vehicle_code="veh002",
                    reg_number="KA02BC2345",
                    status="INACTIVE",
                    rc_card_url="https://example.com/rc/veh002.pdf"
                ),
                Vehicle(
                    vendor_id=vendors[1].vendor_id,
                    vehicle_type_id=vehicle_types[2].vehicle_type_id,
                    driver_id=drivers[2].driver_id,
                    vehicle_code="veh003",
                    reg_number="KA03CD3456",
                    status="MAINTENANCE",
                    rc_card_url="https://example.com/rc/veh003.pdf"
                ),
            ]
            session.add_all(vehicles)
            session.flush()

            # --- Seed Devices ---
            devices = [
                Device(
                    employee_id=drivers[0].driver_id,
                    device_uuid="uuid-101-aaa",
                    device_name="John's iPhone",
                    access_token="token101",
                    fcm_token="fcm_token_101"
                ),
                Device(
                    employee_id=drivers[1].driver_id,
                    device_uuid="uuid-102-bbb",
                    device_name="Alice's Android",
                    access_token="token102",
                    fcm_token="fcm_token_102"
                ),
                Device(
                    employee_id=drivers[2].driver_id,
                    device_uuid="uuid-103-ccc",
                    device_name="Bob's Tablet",
                    access_token="token103",
                    fcm_token="fcm_token_103"
                ),
            ]
            session.add_all(devices)
            session.flush()
            session.commit()
            print("Sample data seeded successfully.")
        except IntegrityError as e:
            print(f"Error seeding data: {e}")
            session.rollback()
        except Exception as e:
            print(f"Unexpected error seeding data: {e}")
            session.rollback()
            raise e
    finally:
        session.close()