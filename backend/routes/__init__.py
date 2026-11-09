"""All blueprints are registered here. Each later step adds one line."""
from routes.auth import auth_bp
from routes.exports import exports_bp
from routes.health import health_bp
from routes.imports import imports_bp
from routes.master import master_bp
from routes.products import products_bp
from routes.samples import samples_bp
from routes.search import search_bp
from routes.users import users_bp
from routes.workflow import workflow_bp


def register_blueprints(app):
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(samples_bp, url_prefix="/api/samples")
    app.register_blueprint(workflow_bp, url_prefix="/api/samples")
    app.register_blueprint(master_bp, url_prefix="/api/master")
    app.register_blueprint(exports_bp, url_prefix="/api/export")
    app.register_blueprint(imports_bp, url_prefix="/api/import")
    app.register_blueprint(search_bp, url_prefix="/api/search")
