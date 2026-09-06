import os
from dotenv import load_dotenv
from app import app

if __name__ == "__main__":
    # Ensure environment is loaded for local run
    load_dotenv()
    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"Starting ClassOps backend via main.py on port {port}")
    app.run(host="0.0.0.0", port=port)
