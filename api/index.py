# Vercel Python Serverless entrypoint
# Exposes the Flask app from app.py as a handler
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Import the Flask app
from app import app as flask_app

# Vercel looks for a module-level variable named `app`
app = flask_app

# Optional local run for testing this entrypoint directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    run_simple("0.0.0.0", port, app, use_reloader=True, use_debugger=True)
