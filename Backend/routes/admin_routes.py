from flask import Blueprint, request
from controllers import admin_controller, rbac_controller

admin_bp = Blueprint("admin", __name__)

# Admin UI
@admin_bp.route("/admin", methods=["GET"])
def admin_dashboard():
    return admin_controller.serve_admin_ui()

# Admin Auth API
@admin_bp.route("/api/admin/login", methods=["POST"])
def admin_login():
    return admin_controller.admin_login()

@admin_bp.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    return admin_controller.admin_logout()

# Admin Protected APIs for the dashboard
@admin_bp.route("/api/admin/roles", methods=["GET"])
def get_roles():
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return rbac_controller.get_roles()

@admin_bp.route("/api/admin/roles", methods=["POST"])
def create_role():
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return rbac_controller.create_role()

@admin_bp.route("/api/admin/roles/<role_name>", methods=["PUT"])
def update_role(role_name):
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return rbac_controller.update_role(role_name)

@admin_bp.route("/api/admin/roles/<role_name>", methods=["DELETE"])
def delete_role(role_name):
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return rbac_controller.delete_role(role_name)

@admin_bp.route("/api/admin/components", methods=["GET"])
def get_components():
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return admin_controller.get_components()

@admin_bp.route("/api/admin/assignments", methods=["GET"])
def get_assignments():
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return rbac_controller.get_role_assignments()

@admin_bp.route("/api/admin/assignments", methods=["POST"])
def create_assignment():
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return rbac_controller.create_role_assignment()

@admin_bp.route("/api/admin/assignments/<email>", methods=["DELETE"])
def delete_assignment(email):
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return rbac_controller.delete_role_assignment(email)

@admin_bp.route("/api/admin/bulk-import", methods=["POST"])
def bulk_import():
    auth_err = admin_controller.check_admin_auth()
    if auth_err: return auth_err
    return rbac_controller.bulk_import()
