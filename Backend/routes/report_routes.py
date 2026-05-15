from flask import Blueprint
from controllers import report_controller
from utils.rbac_middleware import require_permission

report_bp = Blueprint("report", __name__)


@report_bp.route("/api/metrics/compliance", methods=["GET"])
@require_permission(module="overview", permission="view")
def get_compliance_metrics():
    return report_controller.get_compliance_metrics()


@report_bp.route("/api/reports/compliance.pdf", methods=["GET"])
@require_permission(module="overview", permission="view")
def generate_compliance_report():
    return report_controller.generate_compliance_report()
