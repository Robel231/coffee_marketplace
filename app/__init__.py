from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bootstrap = Bootstrap()

# Configure Flask-Login
login_manager.login_view = "main.login"
login_manager.session_protection = "strong"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)

    # Import and register Blueprints
    from app.routes import bp
    app.register_blueprint(bp)

    return app
