from fastapi import Request, HTTPException, status
from typing import List

class PermissionChecker:
    def __init__(
        self,
        required_permissions: List[str],
        check_tenant: bool = True
    ):
        self.required_permissions = required_permissions
        self.check_tenant = check_tenant
    
    async def __call__(self, request: Request):
        user = request.state.user
        
        # Check if user has required permissions
        user_permissions = [p["module"] + "." + a 
                          for p in user["permissions"]
                          for a in p["action"]]
        
        if not any(p in user_permissions for p in self.required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Check tenant access if required
        if self.check_tenant:
            tenant_id = request.path_params.get("tenant_id")
            if tenant_id and tenant_id != user["tenant_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to this tenant is forbidden"
                )
      
def require_permissions(
    permissions: List[str],
    check_tenant: bool = True,
    tenant_id_param: str = "tenant_id"
):
    """Decorator for requiring permissions"""
    checker = PermissionChecker(permissions, check_tenant, tenant_id_param)
    return checker