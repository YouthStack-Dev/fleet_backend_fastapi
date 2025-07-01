from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL","postgresql://servicemgr_user:password@localhost:5433/servicemgr_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def     get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_data():
    session = SessionLocal()
    try:
        from app.database.models import Tenant, User, Group, Role, Service, Policy, user_tenant, group_user, group_role, user_role

        # Create Tenants
        tenant1 = Tenant(name="Tenant Alpha", tenant_metadata={"industry": "Finance"})
        tenant2 = Tenant(name="Tenant Beta", tenant_metadata={"industry": "Healthcare"})

        session.add_all([tenant1, tenant2])
        session.commit()

        # Create Users
        user1 = User(username="alice", email="alice@example.com", hashed_password="hashedpwd1", full_name="Alice Smith")
        user2 = User(username="bob", email="bob@example.com", hashed_password="hashedpwd2", full_name="Bob Jones")
        user3 = User(username="carol", email="carol@example.com", hashed_password="hashedpwd3", full_name="Carol White")

        session.add_all([user1, user2, user3])
        session.commit()

        # Associate Users with Tenants
        session.execute(user_tenant.insert(), [
            {"user_id": user1.id, "tenant_id": tenant1.id, "metadata": json.dumps({"role": "admin"})},
            {"user_id": user2.id, "tenant_id": tenant1.id, "metadata": json.dumps({"role": "member"})},
            {"user_id": user2.id, "tenant_id": tenant2.id, "metadata": json.dumps({"role": "admin"})},
            {"user_id": user3.id, "tenant_id": tenant2.id, "metadata": json.dumps({"role": "member"})},
        ])
        session.commit()

        # Create Groups
        group1 = Group(name="Admins", tenant_id=tenant1.id, description="Admin Group for Tenant Alpha")
        group2 = Group(name="Users", tenant_id=tenant1.id, description="User Group for Tenant Alpha")
        group3 = Group(name="Admins", tenant_id=tenant2.id, description="Admin Group for Tenant Beta")

        session.add_all([group1, group2, group3])
        session.commit()

        # Assign Users to Groups
        session.execute(group_user.insert(), [
            {"group_id": group1.id, "user_id": user1.id},
            {"group_id": group2.id, "user_id": user2.id},
            {"group_id": group3.id, "user_id": user2.id},
            {"group_id": group3.id, "user_id": user3.id},
        ])
        session.commit()

        # Create Roles
        role1 = Role(name="Owner", tenant_id=tenant1.id, description="Owner Role in Tenant Alpha")
        role2 = Role(name="Editor", tenant_id=tenant1.id, description="Editor Role in Tenant Alpha")
        role3 = Role(name="Viewer", tenant_id=tenant2.id, description="Viewer Role in Tenant Beta")

        session.add_all([role1, role2, role3])
        session.commit()

        # Assign Groups to Roles
        session.execute(group_role.insert(), [
            {"group_id": group1.id, "role_id": role1.id},
            {"group_id": group2.id, "role_id": role2.id},
            {"group_id": group3.id, "role_id": role3.id},
        ])
        session.commit()

        # Assign Users to Roles (with tenant context)
        session.execute(user_role.insert(), [
            {"user_id": user1.id, "role_id": role1.id, "tenant_id": tenant1.id},
            {"user_id": user2.id, "role_id": role2.id, "tenant_id": tenant1.id},
            {"user_id": user3.id, "role_id": role3.id, "tenant_id": tenant2.id},
        ])
        session.commit()

        # Create Services
        service1 = Service(name="StorageService", description="Cloud Storage", service_metadata={"tier": "premium"})
        service2 = Service(name="EmailService", description="Transactional Email", service_metadata={"tier": "basic"})

        session.add_all([service1, service2])
        session.commit()

        # Create Policies
        policy1 = Policy(
            tenant_id=tenant1.id, service_id=service1.id, resource="bucket1",
            action="read", group_id=group1.id, condition={"ip_range": "10.0.0.0/8"}
        )
        policy2 = Policy(
            tenant_id=tenant1.id, service_id=service2.id, resource="mailbox1",
            action="write", user_id=user2.id, condition=None
        )
        policy3 = Policy(
            tenant_id=tenant2.id, service_id=service1.id, resource="bucket2",
            action="read", role_id=role3.id, condition=None
        )

        session.add_all([policy1, policy2, policy3])
        session.commit()

        print("Sample data seeded successfully.")
    except Exception as e:
        print("Error seeding sample data:", e)
        session.rollback()
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