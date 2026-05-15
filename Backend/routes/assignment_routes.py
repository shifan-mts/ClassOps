from flask import Blueprint
from controllers import assignment_controller
from utils.rbac_middleware import require_permission

assignment_bp = Blueprint("assignment", __name__)


@assignment_bp.route("/api/courses/<course_id>/sync-assignments", methods=["POST"])
@require_permission(module="ai-tools", permission="manage")
def sync_assignments(course_id):
    return assignment_controller.sync_assignments(course_id)


@assignment_bp.route("/api/courses/<course_id>/assignments", methods=["GET"])
@require_permission(module="teacher-dashboard", permission="view")
def get_assignments(course_id):
    return assignment_controller.get_assignments(course_id)


@assignment_bp.route("/api/assignments/check", methods=["POST"])
@require_permission(module="ai-tools", permission="edit")
def check_plagiarism():
    return assignment_controller.check_plagiarism()


@assignment_bp.route("/api/courses/<course_id>/assignments/<assignment_id>/submissions", methods=["GET"])
@require_permission(module="evaluation", permission="view")
def get_submissions(course_id, assignment_id):
    return assignment_controller.get_submissions(course_id, assignment_id)


@assignment_bp.route("/api/courses/<course_id>/assignments/<assignment_id>/submissions/<student_id>/feedback", methods=["POST"])
@require_permission(module="evaluation", permission="edit")
def save_feedback(course_id, assignment_id, student_id):
    return assignment_controller.save_feedback(course_id, assignment_id, student_id)


@assignment_bp.route("/api/courses/<course_id>/assignments/<assignment_id>/analyze", methods=["POST"])
@require_permission(module="ai-tools", permission="edit")
def analyze_submissions(course_id, assignment_id):
    return assignment_controller.analyze_submissions(course_id, assignment_id)
