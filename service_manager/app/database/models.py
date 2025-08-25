from sqlalchemy import (
    Boolean, Column, String, Integer, ForeignKey, DateTime, JSON, Text, UniqueConstraint, Table, Date, text
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from app.database.database import Base, TimestampMixin
from sqlalchemy.dialects.postgresql import JSONB

# Association tables
user_tenant = Table(
    'user_tenant',
    Base.metadata,
    Column('user_id', ForeignKey('users.user_id'), primary_key=True),
    Column('tenant_id', ForeignKey('tenants.tenant_id'), primary_key=True),
    Column('metadata', JSON, nullable=True),
    Column('joined_at', DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint('user_id', 'tenant_id', name='uix_user_tenant')
)

group_user = Table(
    'group_user',
    Base.metadata,
    Column('group_id', ForeignKey('groups.group_id'), primary_key=True),
    Column('user_id', ForeignKey('users.user_id'), primary_key=True)
)

group_role = Table(
    'group_role',
    Base.metadata,
    Column('group_id', ForeignKey('groups.group_id'), primary_key=True),
    Column('role_id', ForeignKey('roles.role_id'), primary_key=True),
    UniqueConstraint('group_id', 'role_id', name='uix_group_role')
)

user_role = Table(
    'user_role',
    Base.metadata,
    Column('user_id', ForeignKey('users.user_id'), primary_key=True),
    Column('role_id', ForeignKey('roles.role_id'), primary_key=True),
    Column('tenant_id', ForeignKey('tenants.tenant_id'), primary_key=True),
    UniqueConstraint('user_id', 'role_id', 'tenant_id', name='uix_user_role')
)



class Tenant(Base, TimestampMixin):
    __tablename__ = 'tenants'
    tenant_id = Column(Integer, primary_key=True)
    tenant_name = Column(String(255), unique=True, nullable=False)
    address = Column(String(500), nullable=True)
    longitude = Column(String(50), nullable=True)
    latitude = Column(String(50), nullable=True)
    tenant_metadata = Column(JSON, nullable=True)
    is_active = Column(Integer, default=1)

    users = relationship("User", secondary=user_tenant, back_populates="tenants")
    groups = relationship("Group", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")
    cutoff = relationship("Cutoff", back_populates="tenant", uselist=False)
    shifts = relationship("Shift", back_populates="tenant")
    vendors = relationship("Vendor", back_populates="tenant")
    employees = relationship("Employee", back_populates="tenant")
    bookings = relationship("Booking", back_populates="tenant")


class User(Base, TimestampMixin):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.tenant_id'), nullable=False)
    username = Column(String(100), nullable=False)
    mobile_number = Column(String(15), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Stores hashed password
    is_active = Column(Boolean, default=True)

    tenants = relationship("Tenant", secondary=user_tenant, back_populates="users")
    groups = relationship("Group", secondary=group_user, back_populates="users")
    roles = relationship("Role", secondary=user_role, back_populates="users")
    

class Department(Base, TimestampMixin):
    __tablename__ = 'departments'

    department_id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.tenant_id'), nullable=False)
    department_name = Column(String(255), nullable=False)
    description = Column(String(500))

    tenant = relationship("Tenant", backref="departments")
    employees = relationship("Employee", back_populates="department")
    bookings = relationship("Booking", back_populates="department")

    __table_args__ = (
        UniqueConstraint('department_name', 'tenant_id', name='uix_department_tenant'),
    )

class Employee(Base, TimestampMixin):
    __tablename__ = 'employees'
    employee_id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True, nullable=False )  # For 'sam1', etc.
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    mobile_number = Column(String(15), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)  # Stores hashed password
    department_id = Column(Integer, ForeignKey('departments.department_id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.tenant_id'), nullable=False)
    gender = Column(String(50))
    alternate_mobile_number = Column(String(15))
    office = Column(String(255))
    special_need = Column(String, nullable=True)  # Enum recommended for future
    special_need_start_date = Column(Date, nullable=True)
    special_need_end_date = Column(Date, nullable=True)
    subscribe_via_email = Column(Boolean, default=False)
    subscribe_via_sms = Column(Boolean, default=False)
    address = Column(String(500))
    latitude = Column(String(50))
    longitude = Column(String(50))
    landmark = Column(String(255))
    is_active = Column(Boolean, default=True)   # 👈 Add this

    tenant = relationship("Tenant", back_populates="employees")
    department = relationship("Department", back_populates="employees")
    device = relationship("Device", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="employee")




class Group(Base, TimestampMixin):
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True)
    group_name = Column(String(100), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.tenant_id'), nullable=False)
    description = Column(String(200))

    tenant = relationship("Tenant", back_populates="groups")
    users = relationship("User", secondary=group_user, back_populates="groups")
    roles = relationship("Role", secondary=group_role, back_populates="groups")  # Fixed this line

    __table_args__ = (UniqueConstraint('group_name', 'tenant_id', name='uix_group_tenant'),)

class Role(Base, TimestampMixin):
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(200))
    tenant_id = Column(Integer, ForeignKey('tenants.tenant_id'), nullable=False)

    tenant = relationship("Tenant", back_populates="roles")
    groups = relationship("Group", secondary=group_role, back_populates="roles")
    users = relationship("User", secondary=user_role, back_populates="roles")

    __table_args__ = (UniqueConstraint('role_name', 'tenant_id', name='uix_role_name_tenant'),)

class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String, nullable=True)
    service_metadata = Column(JSON, nullable=True)
    onboarded_at = Column(DateTime(timezone=True), server_default=func.now())

class Module(Base):
    __tablename__ = 'modules'
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)


class Policy(Base):
    __tablename__ = 'policies'

    policy_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.tenant_id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=True)
    can_view = Column(Boolean, default=False)
    can_create = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    group_id = Column(Integer, ForeignKey('groups.group_id'), nullable=True)
    role_id = Column(Integer, ForeignKey('roles.role_id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    condition = Column(JSON, nullable=True)

    tenant = relationship("Tenant")
    service = relationship("Service")
    group = relationship("Group")
    role = relationship("Role")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'service_id', 'module_id', 'group_id', 'role_id', 'user_id',
            name='uix_policy'
        ),
    )

class Cutoff(Base):
    __tablename__ = "cutoff"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False, unique=True)

    booking_cutoff = Column(Integer, nullable=False, default=6)
    cancellation_cutoff = Column(Integer, nullable=False, default=6)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to Tenant
    tenant = relationship("Tenant", back_populates="cutoff")

from sqlalchemy import Column, Integer, String, Time, Enum, Boolean, ForeignKey
import enum

class LogType(str, enum.Enum):
    IN = "in"
    OUT = "out"

class DayOfWeek(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class PickupType(str, enum.Enum):
    PICKUP = "pickup"
    NODAL = "nodal"

class GenderType(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    ANY = "any"

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)

    shift_code = Column(String, nullable=False)
    log_type = Column(Enum(LogType), nullable=False)
    shift_time = Column(Time, nullable=False)
    day = Column(String, nullable=False)
    waiting_time_minutes = Column(Integer, nullable=False)
    pickup_type = Column(Enum(PickupType), nullable=False)
    gender = Column(Enum(GenderType), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship to Tenant
    tenant = relationship("Tenant", back_populates="shifts")
    bookings = relationship("Booking", back_populates="shift")
    shift_routes = relationship("ShiftRoute", back_populates="shift", cascade="all, delete-orphan")


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    vendor_name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to Tenant
    tenant = relationship("Tenant", back_populates="vendors")
    vehicle_types = relationship("VehicleType", back_populates="vendor", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="vendor", cascade="all, delete-orphan")
    drivers = relationship("Driver", back_populates="vendor", cascade="all, delete-orphan")

class FuelType(str, enum.Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    CNG = "cng"
    HYBRID = "hybrid"

class VehicleType(Base):
    __tablename__ = "vehicle_types"

    vehicle_type_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    capacity = Column(Integer, nullable=False)
    fuel_type = Column(Enum(FuelType), nullable=False)

    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    vendor = relationship("Vendor", back_populates="vehicle_types")
    vehicles = relationship("Vehicle", back_populates="vehicle_type")

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False)
    vehicle_type_id = Column(Integer, ForeignKey("vehicle_types.vehicle_type_id", ondelete="SET NULL"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id", ondelete="SET NULL"), nullable=True)

    vehicle_code = Column(String, nullable=False, unique=True, comment="App-managed vehicle code")
    reg_number = Column(String, nullable=False, unique=True, comment="Physical vehicle registration number")

    status = Column(String, nullable=False, default="ACTIVE", comment="Vehicle status like ACTIVE, INACTIVE, MAINTENANCE")

    rc_card_url = Column(String, nullable=True, comment="URL to RC card document")
    rc_expiry_date = Column(Date, nullable=True, comment="RC card expiry date")
    insurance_expiry_date = Column(Date, nullable=True, comment="Insurance expiry date")
    insurance_url = Column(String, nullable=True, comment="URL to insurance document")
    permit_url = Column(String, nullable=True, comment="URL to permit document")
    permit_expiry_date = Column(Date, nullable=True, comment="Permit expiry date")
    pollution_expiry_date = Column(Date, nullable=True, comment="Pollution certificate expiry date")
    pollution_url = Column(String, nullable=True, comment="URL to pollution certificate")
    fitness_url = Column(String, nullable=True, comment="URL to fitness certificate")
    fitness_expiry_date = Column(Date, nullable=True, comment="Fitness certificate expiry date")
    tax_receipt_date = Column(Date, nullable=True, comment="Tax receipt date")
    tax_receipt_url = Column(String, nullable=True, comment="URL to tax receipt")

    description = Column(Text, nullable=True, comment="Optional description or remarks about the vehicle")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    vendor = relationship("Vendor", back_populates="vehicles")
    driver = relationship("Driver", back_populates="vehicles", uselist=False)
    vehicle_type = relationship("VehicleType", back_populates="vehicles")


class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(Integer, primary_key=True, index=True)
    
    driver_code = Column(String(50), nullable=False)  # e.g., 'drv1', 'acm1'

    # Unique fields managed within this table
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    mobile_number = Column(String(20), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)  # Stores hashed password
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False)

    city = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)

    alternate_mobile_number = Column(String(20), nullable=True)
    permanent_address = Column(String(255), nullable=True)
    current_address = Column(String(255), nullable=True)

    bgv_status = Column(String(50), default="Pending")
    bgv_date = Column(Date, nullable=True)
    bgv_doc_url = Column(String(255), nullable=True)  

    police_verification_status = Column(String(50), default="Pending")
    police_verification_date = Column(Date, nullable=True)
    police_verification_doc_url = Column(String(255), nullable=True)

    medical_verification_status = Column(String(50), default="Pending")
    medical_verification_date = Column(Date, nullable=True)
    medical_verification_doc_url = Column(String(255), nullable=True)

    training_verification_status = Column(String(50), default="Pending")
    training_verification_date = Column(Date, nullable=True)
    training_verification_doc_url = Column(String(255), nullable=True)

    eye_test_verification_status = Column(String(50), default="Pending")
    eye_test_verification_date = Column(Date, nullable=True)
    eye_test_verification_doc_url = Column(String(255), nullable=True)

    license_number = Column(String(20), nullable=True)
    license_expiry_date = Column(Date, nullable=True)
    license_doc_url = Column(String(255), nullable=True)

    photo_url = Column(String(255), nullable=True)
    
    induction_date = Column(Date, nullable=True)
    induction_doc_url = Column(String(255), nullable=True)

    badge_number = Column(String(20), nullable=True)
    badge_expiry_date = Column(Date, nullable=True)
    badge_doc_url = Column(String(255), nullable=True)

    alternate_govt_id = Column(String(20), nullable=True)
    alternate_govt_id_doc_type = Column(String(50), nullable=True)
    alternate_govt_id_doc_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    # user = relationship("User", back_populates="driver")
    vendor = relationship("Vendor", back_populates="drivers")
    vehicles = relationship("Vehicle", back_populates="driver")


# Note: The Device model is used to manage devices associated with users, such as mobile devices for push notifications.
class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False, unique=True)
    device_uuid = Column(String(255), nullable=False)
    access_token = Column(String(512), nullable=True)
    device_name = Column(String(255), nullable=True)
    fcm_token = Column(String(512), nullable=True)  # Optional for push notifications

    employee = relationship("Employee", back_populates="device", uselist=False)


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    employee_code = Column(String(50), nullable=False)  # e.g., 'sam1', etc.
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=False)
    booking_date = Column(Date, nullable=False)  # Date of the booking
    pickup_location = Column(String(255), nullable=False)
    pickup_location_latitude = Column(String(50), nullable=False)
    pickup_location_longitude = Column(String(50), nullable=False)
    drop_location = Column(String(255), nullable=False)
    drop_location_latitude = Column(String(50), nullable=False)
    drop_location_longitude = Column(String(50), nullable=False)
    status = Column(String(50), default="Pending")  # e.g., Pending, Confirmed, Completed, Cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    employee = relationship("Employee", back_populates="bookings")
    tenant = relationship("Tenant", back_populates="bookings")
    shift = relationship("Shift", back_populates="bookings")
    department = relationship("Department", back_populates="bookings")


class ShiftRoute(Base):
    __tablename__ = "shift_routes"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    route_date = Column(Date, nullable=False)
    route_number = Column(Integer, nullable=False)
    route_data = Column(JSONB, nullable=False)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    shift = relationship("Shift", back_populates="shift_routes")