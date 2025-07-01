from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.api.schemas.schemas import PolicyCreate, PolicyRead
from app.controller.policy_controller import PolicyController
from common_utils.auth.permission_checker import PermissionChecker

router = APIRouter()
policy_controller = PolicyController()

@router.post("/", response_model=PolicyRead)
async def create_policy(
    policy: PolicyCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["policy_management.create"]))
):
    try:
        return policy_controller.create_policy(policy, db)
    except HTTPException as e:
        raise e

@router.get("/", response_model=list[PolicyRead])
async def get_policies(
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["policy_management.read"])),
    skip: int = 0,
    limit: int = 100,
    tenant_id: int = None,
    service_id: int = None,
    group_id: int = None,
    role_id: int = None,
    user_id: int = None
):
    return policy_controller.get_policies(
        db, skip, limit, tenant_id, service_id, group_id, role_id, user_id
    )

@router.get("/{policy_id}", response_model=PolicyRead)
async def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["policy_management.read"]))
):
    policy = policy_controller.get_policy(policy_id, db)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@router.put("/{policy_id}", response_model=PolicyRead)
async def update_policy(
    policy_id: int,
    policy_update: PolicyCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["policy_management.update"]))
):
    try:
        policy = policy_controller.update_policy(policy_id, policy_update, db)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy
    except HTTPException as e:
        raise e

@router.patch("/{policy_id}", response_model=PolicyRead)
async def patch_policy(
    policy_id: int,
    policy_update: dict,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["policy_management.update"]))
):
    try:
        policy = policy_controller.patch_policy(policy_id, policy_update, db)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy
    except HTTPException as e:
        raise e

@router.delete("/{policy_id}", response_model=PolicyRead)
async def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(PermissionChecker(["policy_management.delete"]))
):
    try:
        policy = policy_controller.delete_policy(policy_id, db)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy
    except HTTPException as e:
        raise e