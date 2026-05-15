from flask import Blueprint
from controllers import qp_controller
from utils.rbac_middleware import require_permission

qp_bp = Blueprint("question_paper", __name__)


@qp_bp.route("/api/question-paper/generate", methods=["POST"])
@require_permission(module="ai-tools", permission="edit")
def generate_question_paper():
    return qp_controller.generate_question_paper()
