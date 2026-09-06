import logging
import os

from flask_cors import CORS
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix

from config.constants import ALLOWED_CORS_ORIGINS


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _session_cookie_secure_default():
    base_url = os.getenv("BASE_URL", "")
    app_env = os.getenv("APP_ENV", "").strip().lower()
    return app_env == "production" or base_url.startswith("https://") or bool(os.getenv("RENDER"))


def configure_app(app):
    app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or "super_secret_dev_key"
    if _env_bool("TRUST_PROXY", True):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": ALLOWED_CORS_ORIGINS}},
    )

    session_dir = os.getenv("SESSION_FILE_DIR") or os.path.join(app.instance_path, "sessions")
    os.makedirs(session_dir, exist_ok=True)
    app.config.update(
        SESSION_TYPE="filesystem",
        SESSION_FILE_DIR=session_dir,
        SESSION_PERMANENT=True,
        SESSION_USE_SIGNER=True,
        SESSION_COOKIE_SAMESITE=os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
        SESSION_COOKIE_SECURE=_env_bool("SESSION_COOKIE_SECURE", _session_cookie_secure_default()),
        SESSION_COOKIE_HTTPONLY=True,
        PREFERRED_URL_SCHEME="https" if _session_cookie_secure_default() else "http",
    )
    if os.getenv("SESSION_COOKIE_DOMAIN"):
        app.config["SESSION_COOKIE_DOMAIN"] = os.getenv("SESSION_COOKIE_DOMAIN")
    Session(app)

    return app
