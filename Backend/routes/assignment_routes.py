from flask import Blueprint

from controllers import assignment_controller

assignment_bp = Blueprint("assignment", __name__)


@assignment_bp.route("/api/courses/<course_id>/sync-assignments", methods=["POST"])
def sync_assignments(course_id):
    return assignment_controller.sync_assignments(course_id)


@assignment_bp.route("/api/courses/<course_id>/assignments", methods=["GET"])
def get_assignments(course_id):
    return assignment_controller.get_assignments(course_id)


@assignment_bp.route("/api/assignments/check", methods=["POST"])
def check_plagiarism():
    return assignment_controller.check_plagiarism()


@assignment_bp.route("/api/courses/<course_id>/assignments/<assignment_id>/submissions", methods=["GET"])
def get_submissions(course_id, assignment_id):
    return assignment_controller.get_submissions(course_id, assignment_id)


@assignment_bp.route("/api/courses/<course_id>/assignments/<assignment_id>/submissions/<student_id>/feedback", methods=["POST"])
def save_feedback(course_id, assignment_id, student_id):
    return assignment_controller.save_feedback(course_id, assignment_id, student_id)


@assignment_bp.route("/api/courses/<course_id>/assignments/<assignment_id>/analyze", methods=["POST"])
def analyze_submissions(course_id, assignment_id):
    return assignment_controller.analyze_submissions(course_id, assignment_id)
