# from sqlalchemy.orm import Session
# from fastapi import HTTPException
# from app.api.schemas.schemas import GroupCreate, AssignPolicyRequest, PolicyRead
# from app.crud import crud

# class PolicyController:
#     def create_group(self, group: GroupCreate, db: Session):
#         return crud.create_group(db, group)

#     def assign_policy(self, req: AssignPolicyRequest, db: Session):
#         crud.assign_policy_to_group(db, req)
#         return {"assigned": True}

#     def remove_policy(self, req: AssignPolicyRequest, db: Session):
#         crud.remove_policy_from_group(db, req.group_id, req.policy_id)
#         return {"removed": True}

#     def get_policies(self, db: Session, skip: int = 0, limit: int = 100, **filters):
#         return crud.get_policies(db, skip=skip, limit=limit, **filters)

#     def get_policy(self, policy_id: int, db: Session):
#         policy = crud.get_policy(db, policy_id)
#         if not policy:
#             raise HTTPException(status_code=404, detail="Policy not found")
#         return policy

#     def update_policy(self, policy_id: int, policy_update: PolicyRead, db: Session):
#         updated = crud.update_policy(db, policy_id, policy_update)
#         if not updated:
#             raise HTTPException(status_code=404, detail="Policy not found")
#         return updated

#     def patch_policy(self, policy_id: int, policy_update: dict, db: Session):
#         updated = crud.patch_policy(db, policy_id, policy_update)
#         if not updated:
#             raise HTTPException(status_code=404, detail="Policy not found")
#         return updated

#     def delete_policy(self, policy_id: int, db: Session):
#         deleted = crud.delete_policy(db, policy_id)
#         if not deleted:
#             raise HTTPException(status_code=404, detail="Policy not found")
#         return deleted
