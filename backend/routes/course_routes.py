from flask import Blueprint
from controllers import course_controller
from utils.rbac_middleware import require_permission

course_bp = Blueprint("course", __name__)


@course_bp.route("/api/courses", methods=["GET"])
@require_permission(module="teacher-dashboard", permission="view")
def get_courses():
    return course_controller.get_courses()


@course_bp.route("/api/courses/<course_id>/meeting-config", methods=["GET", "POST"])
@require_permission(module="meet", permission="manage")
def course_meeting_config(course_id):
    return course_controller.course_meeting_config(course_id)


@course_bp.route("/api/courses/<course_id>/sync-students", methods=["POST"])
@require_permission(module="attendance", permission="manage")
def sync_students_for_course(course_id):
    return course_controller.sync_students_for_course(course_id)


@course_bp.route("/api/courses/<course_id>/students", methods=["GET"])
@require_permission(module="attendance", permission="view")
def get_students(course_id):
    return course_controller.get_students(course_id)
