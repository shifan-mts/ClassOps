from flask import Blueprint

from controllers import course_controller

course_bp = Blueprint("course", __name__)


@course_bp.route("/api/courses", methods=["GET"])
def get_courses():
    return course_controller.get_courses()


@course_bp.route("/api/courses/<course_id>/meeting-config", methods=["GET", "POST"])
def course_meeting_config(course_id):
    return course_controller.course_meeting_config(course_id)


@course_bp.route("/api/courses/<course_id>/sync-students", methods=["POST"])
def sync_students_for_course(course_id):
    return course_controller.sync_students_for_course(course_id)


@course_bp.route("/api/courses/<course_id>/students", methods=["GET"])
def get_students(course_id):
    return course_controller.get_students(course_id)
