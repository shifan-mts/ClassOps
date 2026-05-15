from flask import Blueprint
from controllers import rbac_controller
from utils.rbac_middleware import require_permission

rbac_bp = Blueprint("rbac", __name__)

# Apply the require_permission decorator to all routes in this blueprint
# requiring 'admin_settings' 'modify' permission

@rbac_bp.route("/api/roles", methods=["GET"])
@require_permission(module="admin_settings", permission="modify")
def get_roles():
    return rbac_controller.get_roles()

@rbac_bp.route("/api/roles", methods=["POST"])
@require_permission(module="admin_settings", permission="modify")
def create_role():
    return rbac_controller.create_role()

@rbac_bp.route("/api/roles/<role_name>", methods=["PUT"])
@require_permission(module="admin_settings", permission="modify")
def update_role(role_name):
    return rbac_controller.update_role(role_name)

@rbac_bp.route("/api/roles/<role_name>", methods=["DELETE"])
@require_permission(module="admin_settings", permission="modify")
def delete_role(role_name):
    return rbac_controller.delete_role(role_name)

@rbac_bp.route("/api/role-assignments", methods=["GET"])
@require_permission(module="admin_settings", permission="modify")
def get_role_assignments():
    return rbac_controller.get_role_assignments()

@rbac_bp.route("/api/role-assignments", methods=["POST"])
@require_permission(module="admin_settings", permission="modify")
def create_role_assignment():
    return rbac_controller.create_role_assignment()

@rbac_bp.route("/api/role-assignments/<email>", methods=["DELETE"])
@require_permission(module="admin_settings", permission="modify")
def delete_role_assignment(email):
    return rbac_controller.delete_role_assignment(email)

@rbac_bp.route("/api/role-assignments/bulk-delete", methods=["POST"])
@require_permission(module="admin_settings", permission="modify")
def bulk_delete_role_assignments():
    return rbac_controller.bulk_delete_role_assignments()
