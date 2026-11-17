"""Flask application factory and extension initialization.

This module creates the Flask app, loads configurations, and initializes
extensions such as SQLAlchemy, LoginManager, and WTForms CSRF protection.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

# Extensions (initialized later in create_app)
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"
csrf = CSRFProtect()


def create_app():
    """Application factory pattern.

    Returns:
        Flask: Configured Flask application instance.
    """
    # Load environment variables from .env if present
    load_dotenv()

    app = Flask(__name__, instance_relative_config=False)
    # Basic configuration – can be overridden by instance config or env vars
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///kaushalsetu.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Initialise extensions with app context
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import and register blueprints
    from . import routes
    app.register_blueprint(routes.main_bp)

    # Create database tables if they don't exist yet
    with app.app_context():
        db.create_all()

    return app
