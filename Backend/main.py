import os

from dotenv import load_dotenv

from app import create_app


if __name__ == "__main__":
    load_dotenv()
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.logger.info("Starting ClassOps backend on port %s", port)
    app.run(host="0.0.0.0", port=port)
