from flask import Blueprint
from controllers import dashboard_controller
from utils.rbac_middleware import require_permission

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/api/dashboard/stats", methods=["GET"])
@require_permission(module="teacher-dashboard", permission="access")
def get_dashboard_stats():
    return dashboard_controller.get_dashboard_stats()
