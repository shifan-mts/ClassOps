import logging
import os

from flask_cors import CORS
from flask_session import Session

from config.constants import ALLOWED_CORS_ORIGINS


def configure_app(app):
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_dev_key")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": ALLOWED_CORS_ORIGINS}},
    )

    session_dir = os.path.join(app.instance_path, "sessions")
    os.makedirs(session_dir, exist_ok=True)
    app.config.update(
        SESSION_TYPE="filesystem",
        SESSION_FILE_DIR=session_dir,
        SESSION_PERMANENT=True,
        SESSION_USE_SIGNER=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
    )
    Session(app)

    return app
