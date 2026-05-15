from flask import Blueprint
from controllers import student_controller
from utils.rbac_middleware import require_permission

student_bp = Blueprint("student", __name__)


@student_bp.route("/api/student/dashboard", methods=["GET"])
@require_permission(module="student-dashboard", permission="access")
def student_dashboard():
    return student_controller.student_dashboard()


@student_bp.route("/api/student/calendar/sync", methods=["POST"])
@require_permission(module="student-dashboard", permission="edit")
def sync_student_calendar():
    return student_controller.sync_student_calendar()


@student_bp.route("/api/student/evaluation", methods=["POST"])
@require_permission(module="student-dashboard", permission="edit")
def submit_evaluation():
    return student_controller.submit_evaluation()


@student_bp.route("/api/courses/<course_id>/evaluations", methods=["GET"])
@require_permission(module="evaluation", permission="view")
def get_evaluations(course_id):
    return student_controller.get_evaluations(course_id)


@student_bp.route("/api/courses/<course_id>/evaluations/download", methods=["GET"])
@require_permission(module="evaluation", permission="view")
def download_evaluations(course_id):
    return student_controller.download_evaluations(course_id)
