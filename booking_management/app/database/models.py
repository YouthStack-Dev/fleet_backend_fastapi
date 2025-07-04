from sqlalchemy import (
    Column, String, Integer, ForeignKey, DateTime, JSON, UniqueConstraint, Table
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from app.database.database import Base

# Association tables
user_tenant = Table(
    'user_tenant',
    Base.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('tenant_id', ForeignKey('tenants.id'), primary_key=True),
    Column('metadata', JSON, nullable=True),
    Column('joined_at', DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint('user_id', 'tenant_id', name='uix_user_tenant')
)

group_user = Table(
    'group_user',
    Base.metadata,
    Column('group_id', ForeignKey('groups.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True)
)

group_role = Table(
    'group_role',
    Base.metadata,
    Column('group_id', ForeignKey('groups.id'), primary_key=True),
    Column('role_id', ForeignKey('roles.id'), primary_key=True),
    UniqueConstraint('group_id', 'role_id', name='uix_group_role')
)

user_role = Table(
    'user_role',
    Base.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('role_id', ForeignKey('roles.id'), primary_key=True),
    Column('tenant_id', ForeignKey('tenants.id'), primary_key=True),
    UniqueConstraint('user_id', 'role_id', 'tenant_id', name='uix_user_role')
)

class Tenant(Base):
    __tablename__ = 'tenants'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    tenant_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", secondary=user_tenant, back_populates="tenants")
    groups = relationship("Group", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)

    tenants = relationship("Tenant", secondary=user_tenant, back_populates="users")
    groups = relationship("Group", secondary=group_user, back_populates="users")
    roles = relationship("Role", secondary=user_role, back_populates="users")

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    description = Column(String, nullable=True)

    tenant = relationship("Tenant", back_populates="groups")
    users = relationship("User", secondary=group_user, back_populates="groups")
    roles = relationship("Role", secondary=group_role, back_populates="groups")

    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='uix_group_tenant'),)

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    description = Column(String, nullable=True)

    tenant = relationship("Tenant", back_populates="roles")
    groups = relationship("Group", secondary=group_role, back_populates="roles")
    users = relationship("User", secondary=user_role, back_populates="roles")

    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='uix_role_tenant'),)

class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String, nullable=True)
    service_metadata = Column(JSON, nullable=True)
    onboarded_at = Column(DateTime(timezone=True), server_default=func.now())

class Policy(Base):
    __tablename__ = 'policies'
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    resource = Column(String(255), nullable=True)
    action = Column(String(50), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    condition = Column(JSON, nullable=True)

    tenant = relationship("Tenant")
    service = relationship("Service")
    group = relationship("Group")
    role = relationship("Role")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'service_id', 'resource', 'action', 'group_id', 'role_id', 'user_id',
            name='uix_policy'
        ),
    )