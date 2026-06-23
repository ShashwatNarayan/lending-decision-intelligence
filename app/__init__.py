"""Flask application factory for the Lending Decision Intelligence Platform.

No auth, no CSRF, no mail — this is a B2B internal tool with no user login.
"""
from flask import Flask, jsonify

from flask_migrate import Migrate

from .config import Config
from .database import db

migrate = Migrate()


def create_app():
    """Build and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so their tables are registered on db.metadata
    # (required for Flask-Migrate autogenerate).
    from .models import db_models  # noqa: F401

    # Blueprints
    from .routes.main import main_bp
    from .routes.portfolio import portfolio_bp
    from .routes.applicant import applicant_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(applicant_bp)

    # JSON error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify(error="Not found"), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify(error="Internal server error"), 500

    return app
