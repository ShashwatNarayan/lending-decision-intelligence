"""Development entry point. Never used in production."""
# Never used in production.
import sys

# UTF-8 stdout fix so ₹ and other non-ASCII chars print on Windows consoles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load .env before importing the app (config reads env vars at import time).
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
