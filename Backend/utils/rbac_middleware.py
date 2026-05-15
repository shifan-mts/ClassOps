from functools import wraps
from flask import session, jsonify

def require_permission(module: str, permission: str):
    """
    Decorator to check if the current user has a specific permission for a given module.
    Expects the user's permissions to be loaded into the session.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = session.get("user")
            if not user:
                return jsonify({"error": "Unauthorized. Please log in."}), 401
            
            permissions = user.get("permissions", {})
            module_perms = permissions.get(module, [])
            
            if permission not in module_perms:
                return jsonify({"error": f"Forbidden. Missing '{permission}' permission for module '{module}'."}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
