import os
import sys
from dotenv import load_dotenv
from flask import Flask, send_from_directory

# Ensure Backend directory is in sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Load environment variables early with specific encoding
load_dotenv(os.path.join(BACKEND_DIR, ".env"), encoding="utf-8-sig")

def _env_bool(name, default=False):
    """Helper to get boolean value from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Configure OAuth environment variables before importing components that might use them
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
if _env_bool("ALLOW_INSECURE_OAUTH", _env_bool("IS_LOCAL", True)):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# Imports that depend on environment setup
from config.settings import configure_app
from routes import register_blueprints
from utils.seed_roles import seed_default_roles

def create_app():
    """Application factory for ClassOps."""
    flask_app = Flask(__name__, static_folder="dist", static_url_path="")
    
    # Configure security, CORS, and session management
    configure_app(flask_app)
    
    # Seed roles
    seed_default_roles()
    
    # Register all API routes
    register_blueprints(flask_app)
    
    # Serve the frontend application
    @flask_app.route("/")
    def serve():
        return send_from_directory(flask_app.static_folder, "index.html")

    @flask_app.route("/<path:path>")
    def static_proxy(path):
        file_path = os.path.join(flask_app.static_folder, path)
        if os.path.exists(file_path):
            return send_from_directory(flask_app.static_folder, path)
        return send_from_directory(flask_app.static_folder, "index.html")

    return flask_app

# Main application instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    # Local development server
    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"ClassOps Backend starting on port {port}")
    app.run(host="0.0.0.0", port=port)
