from fastapi import Depends, Request, HTTPException, status
from typing import List

from .middleware import JWTAuthMiddleware

class PermissionChecker:
    def __init__(
        self,
        required_permissions: List[str],
        check_tenant: bool = True
    ):
        self.required_permissions = required_permissions
        self.check_tenant = check_tenant
    
    async def __call__(self, request: Request, data = Depends(JWTAuthMiddleware())):
        
        user_data = data[0]
        token = data[1]
        # Check if user has required permissions
        user_permissions = [p["module"] + "." + a 
                          for p in user_data["permissions"]
                          for a in p["action"]]
        
        if not any(p in user_permissions for p in self.required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Check tenant access if required
        if self.check_tenant:
            tenant_id = request.path_params.get("tenant_id")
            if tenant_id and tenant_id != user_data["tenant_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to this tenant is forbidden"
                )

        return user_data