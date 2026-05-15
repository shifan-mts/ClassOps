from flask import Blueprint

from controllers import auth_controller

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/google")
def google_auth():
    return auth_controller.google_auth()


@auth_bp.route("/api/auth/google/url")
def google_auth_url():
    return auth_controller.google_auth_url()


@auth_bp.route("/api/auth/google/callback")
def google_auth_callback():
    return auth_controller.google_auth_callback()


@auth_bp.route("/callback")
def google_auth_callback_alias():
    return auth_controller.google_auth_callback()


@auth_bp.route("/api/me")
def get_me():
    return auth_controller.get_me()


@auth_bp.route("/api/auth/permissions")
def get_permissions():
    return auth_controller.get_permissions()


@auth_bp.route("/api/auth/logout", methods=["POST", "GET"])
def logout():
    return auth_controller.logout()


@auth_bp.route("/api/classroom/sync")
def sync_classroom():
    return auth_controller.sync_classroom()
