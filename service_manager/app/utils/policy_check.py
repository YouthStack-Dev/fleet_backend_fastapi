from fastapi import HTTPException, Request
from typing import Any

def check_policy_access(token_payload: dict, request):
    # Example: policies in token are a list of dicts with "action" and "resource"
    # "action" could be HTTP method, "resource" could be endpoint path
    policies = token_payload.get("policies", [])
    method = request.method.lower()
    path = request.url.path

    # Allow if any policy matches the method and resource (path)
    for policy in policies:
        if (policy.get("action", "").lower() == method and
            (policy.get("resource") == path or policy.get("resource") == "*" or policy.get("resource") in path)):
            return
    from fastapi import HTTPException
    raise HTTPException(status_code=403, detail="Forbidden access")
