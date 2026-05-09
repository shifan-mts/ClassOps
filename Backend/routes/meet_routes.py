from flask import Blueprint

from controllers import meet_controller

meet_bp = Blueprint("meet", __name__)


@meet_bp.route("/api/courses/<course_id>/meet/attendance", methods=["GET"])
def get_course_meet_attendance(course_id):
    return meet_controller.get_course_meet_attendance(course_id)


@meet_bp.route("/api/courses/<course_id>/meet/attendance/export", methods=["GET"])
def export_course_meet_attendance(course_id):
    return meet_controller.export_course_meet_attendance(course_id)
