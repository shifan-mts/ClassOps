from flask import Blueprint

from controllers import target_controller

target_bp = Blueprint("target", __name__)


@target_bp.route("/api/targets", methods=["GET", "POST"])
def manage_targets():
    return target_controller.manage_targets()


@target_bp.route("/api/courses/<course_id>/targets/<target_id>", methods=["PATCH"])
def update_target(course_id, target_id):
    return target_controller.update_target(course_id, target_id)
