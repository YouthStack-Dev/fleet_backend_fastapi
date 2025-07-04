from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.api.schemas.schemas import GroupCreate, AssignPolicyRequest
from app.crud import crud

class GroupController:
    def create_group(self, group: GroupCreate, db: Session):
        return crud.create_group(db, group)

    def get_groups(self, db: Session, skip: int = 0, limit: int = 100):
        return crud.get_groups(db, skip=skip, limit=limit)

    def get_group(self, group_id: int, db: Session):
        group = crud.get_group(db, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group

    def assign_policy(self, req: AssignPolicyRequest, db: Session):
        crud.assign_policy_to_group(db, req)
        return {"assigned": True}

    def remove_policy(self, req: AssignPolicyRequest, db: Session):
        crud.remove_policy_from_group(db, req.group_id, req.policy_id)
        return {"removed": True}

    def update_group(self, group_id: int, group_update: GroupCreate, db: Session):
        updated = crud.update_group(db, group_id, group_update)
        if not updated:
            raise HTTPException(status_code=404, detail="Group not found")
        return updated

    def patch_group(self, group_id: int, group_update: dict, db: Session):
        updated = crud.patch_group(db, group_id, group_update)
        if not updated:
            raise HTTPException(status_code=404, detail="Group not found")
        return updated

    def delete_group(self, group_id: int, db: Session):
        deleted = crud.delete_group(db, group_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Group not found")
        return deleted
