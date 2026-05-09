from flask import Blueprint

from controllers import attendance_controller

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/api/attendance", methods=["GET"])
def get_attendance():
    return attendance_controller.get_attendance()


@attendance_bp.route("/api/attendance", methods=["POST"])
def mark_attendance():
    return attendance_controller.mark_attendance()


@attendance_bp.route("/api/attendance/report/<course_id>", methods=["GET"])
def get_attendance_report(course_id):
    return attendance_controller.get_attendance_report(course_id)
