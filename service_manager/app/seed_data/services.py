# app/seed_data/services.py
from typing import List, Dict

DEFAULT_SERVICES: List[Dict] = [
    {"name": "User Management", "description": "Manage users across tenants"},
    {"name": "Tenant Management", "description": "Manage tenants and onboarding"},
    {"name": "Service Management", "description": "Manage services and permissions"},
    {"name": "Shift Management", "description": "Manage employee shifts"},
    {"name": "Driver Management", "description": "Manage drivers and their BGV"},
]
