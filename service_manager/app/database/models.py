from sqlalchemy import (
    Boolean, Column, String, Integer, ForeignKey, DateTime, JSON, UniqueConstraint, Table, Date
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from app.database.database import Base, TimestampMixin

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
    tenant_metadata = Column(JSON, nullable=True)
    is_active = Column(Integer, default=1)

    users = relationship("User", secondary=user_tenant, back_populates="tenants")
    groups = relationship("Group", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")
    cutoff = relationship("Cutoff", back_populates="tenant", uselist=False)
    shifts = relationship("Shift", back_populates="tenant")
    vendors = relationship("Vendor", back_populates="tenant")
    vehicles = relationship("Vehicle", back_populates="tenant")


class User(Base, TimestampMixin):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.tenant_id'), nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Stores hashed password
    is_active = Column(Integer, default=1)

    tenants = relationship("Tenant", secondary=user_tenant, back_populates="users")
    groups = relationship("Group", secondary=group_user, back_populates="users")
    roles = relationship("Role", secondary=user_role, back_populates="users")
    employee = relationship("Employee", back_populates="user", uselist=False)
    driver = relationship("Driver", back_populates="user", uselist=False)
class Department(Base, TimestampMixin):
    __tablename__ = 'departments'

    department_id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.tenant_id'), nullable=False)
    department_name = Column(String(255), nullable=False)
    description = Column(String(500))

    tenant = relationship("Tenant", backref="departments")

    __table_args__ = (
        UniqueConstraint('department_name', 'tenant_id', name='uix_department_tenant'),
    )

class Employee(Base, TimestampMixin):
    __tablename__ = 'employees'

    employee_code = Column(String(50), unique=True, nullable=False ,primary_key=True)  # For 'sam1', etc.
    user_id = Column(Integer, ForeignKey('users.user_id'), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.department_id'), nullable=False)

    gender = Column(String(50))
    mobile_number = Column(String(15))
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

    user = relationship("User", back_populates="employee", uselist=False)
    department = relationship("Department", backref="employees")


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
    
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id", ondelete="SET NULL"), nullable=True)
    vehicle_type_id = Column(Integer, ForeignKey("vehicle_types.vehicle_type_id", ondelete="SET NULL"), nullable=True)

    vehicle_code = Column(String, nullable=False, unique=True)  # app-managed code
    reg_number = Column(String, nullable=False, unique=True)    # physical vehicle registration number

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    vendor = relationship("Vendor", back_populates="vehicles")
    driver = relationship("Driver", back_populates="vehicles")
    vehicle_type = relationship("VehicleType", back_populates="vehicles")
    tenant = relationship("Tenant", back_populates="vehicles")
    driver = relationship("Driver", back_populates="vehicles", uselist=False)

class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False)

    city = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)  # e.g., male/female/other

    alternate_mobile_number = Column(String(20), nullable=True)
    permanent_address = Column(String(255), nullable=True)
    current_address = Column(String(255), nullable=True)
    bgv_status = Column(String(50), default="Pending")  # e.g., Pending, Cleared, Rejected

    bgv_date = Column(Date, nullable=True)

    police_doc_url = Column(String(255), nullable=True)
    license_doc_url = Column(String(255), nullable=True)
    photo_url = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="driver")
    vendor = relationship("Vendor", back_populates="drivers")
    vehicles = relationship("Vehicle", back_populates="driver")