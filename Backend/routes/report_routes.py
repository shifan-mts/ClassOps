from flask import Blueprint

from controllers import report_controller

report_bp = Blueprint("report", __name__)


@report_bp.route("/api/metrics/compliance", methods=["GET"])
def get_compliance_metrics():
    return report_controller.get_compliance_metrics()


@report_bp.route("/api/reports/compliance.pdf", methods=["GET"])
def generate_compliance_report():
    return report_controller.generate_compliance_report()
