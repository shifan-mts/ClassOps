from flask import Blueprint
from controllers import teacher_controller
from utils.rbac_middleware import require_permission

teacher_bp = Blueprint("teacher", __name__)


@teacher_bp.route("/api/teacher/profile", methods=["GET", "POST"])
def teacher_profile():
    return teacher_controller.teacher_profile()


@teacher_bp.route("/api/timetable/generate", methods=["POST"])
@require_permission(module="timetable", permission="edit")
def generate_timetable():
    return teacher_controller.generate_timetable()


@teacher_bp.route("/api/timetable", methods=["GET"])
@require_permission(module="timetable", permission="access")
def get_timetable():
    return teacher_controller.get_timetable()


@teacher_bp.route("/api/timetable/slot", methods=["POST"])
@require_permission(module="timetable", permission="edit")
def upsert_timetable_slot():
    return teacher_controller.upsert_timetable_slot()


@teacher_bp.route("/api/config/update-key", methods=["POST"])
@require_permission(module="ai-tools", permission="manage")
def update_api_key():
    return teacher_controller.update_api_key()
