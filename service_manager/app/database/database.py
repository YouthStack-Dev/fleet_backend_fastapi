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

def seed_data():
    session = SessionLocal()
    try:
        from app.database.models import Tenant, User, Group, Role, Service, Module, Policy, user_tenant, group_user, group_role, user_role, Department, Employee

        # Check if data already exists
        if session.query(Tenant).first():
            print("Data already exists, skipping seed")
            return

        # Create Tenants
        tenants = [
            Tenant(tenant_name="Acme Corp", tenant_metadata={"industry": "Technology", "size": "Enterprise"}),
            Tenant(tenant_name="Startup Inc", tenant_metadata={"industry": "Retail", "size": "Small"}),
            Tenant(tenant_name="Med Solutions", tenant_metadata={"industry": "Healthcare", "size": "Medium"})
        ]
        
        for tenant in tenants:
            try:
                session.add(tenant)
                session.flush()
            except IntegrityError:
                session.rollback()
                tenant = session.query(Tenant).filter_by(tenant_name=tenant.tenant_name).first()
                if not tenant:
                    raise

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
                Module(service_id=services[0].id, name="user_management", description="Manage user accounts"),
                Module(service_id=services[0].id, name="department_management", description="Manage departments"),
                Module(service_id=services[0].id, name="employee_management", description="Manage employees"),
                Module(service_id=services[0].id, name="group_management", description="Manage user groups"),
                Module(service_id=services[0].id, name="mapping_management", description="Vehicle maintenance tracking"),
                Module(service_id=services[0].id, name="policy_management", description="Handle vehicle reservations"),
                Module(service_id=services[0].id, name="service_management", description="Generate analytics reports"),
                Module(service_id=services[0].id, name="tenant_management", description="Generate analytics reports")
            ]
            session.add_all(modules)
            session.flush()

            # Create Users with different roles  password is dp for all users
            users = [
                User(username="admin", email="admin@acme.com", hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d", 
                     
                     tenant_id=tenants[0].tenant_id, is_active=1),
                    
                User(username="manager", email="manager@startup.com", hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d", 
                     tenant_id=tenants[1].tenant_id, is_active=1),
                User(username="driver", email="driver@medsol.com", hashed_password="a9dc602f9d82bc6720b2b4bb016edcacf7da4b2b453a466b742da743f3cba15d", 
                     tenant_id=tenants[2].tenant_id, is_active=1)
            ]
            session.add_all(users)
            session.flush()



            # Create Departments
            departments = [
                Department(tenant_id=tenants[0].tenant_id, department_name="IT", description="Technology department"),
                Department(tenant_id=tenants[1].tenant_id, department_name="Operations", description="Operations department"),
                Department(tenant_id=tenants[2].tenant_id, department_name="Medical", description="Medical staff department")
            ]
            session.add_all(departments)
            session.flush()

            # Create Employees (Assuming you want to make existing users employees)
            employees = [
                Employee(
                    employee_code="acm1",
                    user_id=users[0].user_id,
                    department_id=departments[0].department_id,
                    gender="Male",
                    mobile_number="9876543210",
                    alternate_mobile_number="9123456789",
                    office="Head Office",
                    special_need=None,
                    subscribe_via_email=True,
                    subscribe_via_sms=False,
                    address="Acme HQ, Tech Park",
                    latitude="12.9716",
                    longitude="77.5946",
                    landmark="Near Big Mall"
                ),
                Employee(
                    employee_code="sta1",
                    user_id=users[1].user_id,
                    department_id=departments[1].department_id,
                    gender="Female",
                    mobile_number="8123456789",
                    alternate_mobile_number=None,
                    office="Main Office",
                    special_need="Wheelchair Access",
                    subscribe_via_email=True,
                    subscribe_via_sms=True,
                    address="Startup Inc, Downtown",
                    latitude="28.7041",
                    longitude="77.1025",
                    landmark="Opposite Metro Station"
                ),
                Employee(
                    employee_code="med1",
                    user_id=users[2].user_id,
                    department_id=departments[2].department_id,
                    gender="Male",
                    mobile_number="7894561230",
                    alternate_mobile_number=None,
                    office="Med Solutions Office",
                    special_need=None,
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
                Group(group_name="Fleet Managers", tenant_id=tenants[1].tenant_id, 
                     description="Vehicle fleet managers"),
                Group(group_name="Drivers", tenant_id=tenants[2].tenant_id, 
                     description="Vehicle operators")
            ]
            session.add_all(groups)
            session.flush()

            # Create Roles
            roles = [
                Role(role_name="Super Admin", description="Full system access", tenant_id=tenants[0].tenant_id),
                Role(role_name="Fleet Manager", description="Fleet management access", tenant_id=tenants[1].tenant_id),
                Role(role_name="Driver", description="Vehicle operator access", tenant_id=tenants[2].tenant_id)
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
                Policy(tenant_id=tenants[1].tenant_id, service_id=services[1].id, module_id=modules[2].id,
                      can_view=True, can_create=True, can_edit=False, can_delete=False,
                      role_id=roles[1].role_id),
                Policy(tenant_id=tenants[2].tenant_id, service_id=services[2].id, module_id=modules[3].id,
                      can_view=True, can_create=False, can_edit=False, can_delete=False,
                      user_id=users[2].user_id)
            ]
            session.add_all(policies)
            session.flush()

            # Create Mappings
            # User-Tenant mappings
            for user, tenant in zip(users, tenants):
                session.execute(user_tenant.insert().values(
                    user_id=user.user_id, 
                    tenant_id=tenant.tenant_id,
                    metadata={"role": "primary"}
                ))

            # Group-User mappings
            for group, user in zip(groups, users):
                session.execute(group_user.insert().values(
                    group_id=group.group_id,
                    user_id=user.user_id
                ))

            # Group-Role mappings
            for group, role in zip(groups, roles):
                session.execute(group_role.insert().values(
                    group_id=group.group_id,
                    role_id=role.role_id
                ))

            # User-Role mappings
            for user, role, tenant in zip(users, roles, tenants):
                session.execute(user_role.insert().values(
                    user_id=user.user_id,
                    role_id=role.role_id,
                    tenant_id=tenant.tenant_id
                ))

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

def init_db():
    print("Creating tables")
    import app.database.models  # Ensure models are imported to create tables

    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized and tables created.")

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e