from routes.assignment_routes import assignment_bp
from routes.attendance_routes import attendance_bp
from routes.auth_routes import auth_bp
from routes.course_routes import course_bp
from routes.meet_routes import meet_bp
from routes.qp_routes import qp_bp
from routes.report_routes import report_bp
from routes.student_routes import student_bp
from routes.target_routes import target_bp
from routes.teacher_routes import teacher_bp
from routes.rbac_routes import rbac_bp
from routes.dashboard_routes import dashboard_bp
from routes.admin_routes import admin_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(meet_bp)
    app.register_blueprint(assignment_bp)
    app.register_blueprint(qp_bp)
    app.register_blueprint(target_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(rbac_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
