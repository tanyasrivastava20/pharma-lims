"""PharmaLIMS backend entry point (application factory)."""
import os

from flask import Flask
from flask_cors import CORS

from config import get_config
from database import init_db
from middleware.auth import init_jwt
from middleware.error_handlers import register_error_handlers
from middleware.request_logging import register_request_logging
from routes import register_blueprints
from utils.logging_setup import setup_logging


def create_app(config_name=None):
    cfg = get_config(config_name)
    cfg.validate()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(cfg)
    app.json.sort_keys = False  # keep "success" first in responses

    os.makedirs(app.instance_path, exist_ok=True)
    if app.config["LOG_TO_FILES"]:
        os.makedirs(app.config["LOG_DIR"], exist_ok=True)
    setup_logging(app)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"], "expose_headers": ["Content-Disposition", "X-Request-ID"]}})
    init_db(app)
    init_jwt(app)
    register_request_logging(app)
    register_error_handlers(app)
    register_blueprints(app)
    # the debug reloader starts a second, idle copy of the program; only the serving copy announces itself
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        app.logger.info("PharmaLIMS backend started (environment: %s)", app.config["ENV_NAME"])
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
