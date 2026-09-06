from flask import Blueprint
from controllers import attendance_controller
from utils.rbac_middleware import require_permission

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/api/attendance", methods=["GET"])
@require_permission(module="attendance", permission="view")
def get_attendance():
    return attendance_controller.get_attendance()


@attendance_bp.route("/api/attendance", methods=["POST"])
@require_permission(module="attendance", permission="edit")
def mark_attendance():
    return attendance_controller.mark_attendance()


@attendance_bp.route("/api/attendance/report/<course_id>", methods=["GET"])
@require_permission(module="attendance", permission="view")
def get_attendance_report(course_id):
    return attendance_controller.get_attendance_report(course_id)
