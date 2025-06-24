from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import GroupCreate, GroupRead, AssignPolicyRequest, PolicyRead
from app.controller.policy_controller import PolicyController
from app.api.routes.auth import token_dependency

router = APIRouter()
policy_controller = PolicyController()

@router.post("/", response_model=GroupRead)
def create_group(
    group: GroupCreate,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return policy_controller.create_group(group, db)

@router.post("/assign_policy")
def assign_policy(
    req: AssignPolicyRequest,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return policy_controller.assign_policy(req, db)

@router.post("/remove_policy")
def remove_policy(
    req: AssignPolicyRequest,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return policy_controller.remove_policy(req, db)

@router.get("/search", response_model=list[PolicyRead])
def get_policies(
    skip: int = 0,
    limit: int = 100,
    tenant_id: int = None,
    service_id: int = None,
    group_id: int = None,
    role_id: int = None,
    user_id: int = None,
    action: str = None,
    resource: str = None,
    token: token_dependency = None,
    db: Session = Depends(get_db)
):
    filters = dict(
        tenant_id=tenant_id,
        service_id=service_id,
        group_id=group_id,
        role_id=role_id,
        user_id=user_id,
        action=action,
        resource=resource,
    )
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    return policy_controller.get_policies(db, skip=skip, limit=limit, **filters)

@router.get("/{policy_id}", response_model=PolicyRead)
def get_policy(
    policy_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return policy_controller.get_policy(policy_id, db)

@router.put("/{policy_id}", response_model=PolicyRead)
def update_policy(
    policy_id: int,
    policy_update: PolicyRead,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return policy_controller.update_policy(policy_id, policy_update, db)

@router.patch("/{policy_id}", response_model=PolicyRead)
def patch_policy(
    policy_id: int,
    policy_update: dict,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return policy_controller.patch_policy(policy_id, policy_update, db)

@router.delete("/{policy_id}", response_model=PolicyRead)
def delete_policy(
    policy_id: int,
    token: token_dependency,
    db: Session = Depends(get_db)
):
    return policy_controller.delete_policy(policy_id, db)