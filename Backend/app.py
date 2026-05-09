import os
import sys

from dotenv import load_dotenv
from flask import Flask, send_from_directory

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BACKEND_DIR, ".env"))
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

from config.settings import configure_app  # noqa: E402
from routes import register_blueprints  # noqa: E402


def register_static_routes(app):
    @app.route("/")
    def serve():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:path>")
    def static_proxy(path):
        file_path = os.path.join(app.static_folder, path)
        if os.path.exists(file_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")


def create_app():
    flask_app = Flask(__name__, static_folder="dist", static_url_path="")
    configure_app(flask_app)
    register_static_routes(flask_app)
    register_blueprints(flask_app)
    return flask_app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.logger.info("Starting ClassOps backend on port %s", port)
    app.run(host="0.0.0.0", port=port)
