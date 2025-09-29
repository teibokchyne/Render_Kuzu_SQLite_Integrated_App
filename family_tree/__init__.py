import logging
import os

from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy import text

from family_tree.config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class = Config):
    app = Flask(__name__)

    # Override with test config if provided
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    init_logging(app)

    # Set up login manager
    login_manager.login_view = 'common.login'
    login_manager.login_message_category = 'info'
    
    # User loader function
    @login_manager.user_loader
    def load_user(user_id):
        from family_tree.models import User
        return User.query.get(int(user_id))

    # Import models so they are registered with SQLAlchemy
    from family_tree.models import (
        User, 
        GenderEnum,
        Person,
        Address,
        ImportantDateTypeEnum,
        ImportantDates,
        ContactDetails,
        RelativesTypeEnum,
        Relatives
    )

    # Enable foreign keys on SQLite
    @app.before_request
    def _enable_foreign_keys():
        db.session.execute(text('PRAGMA foreign_keys = ON'))

    # Register blueprints
    from family_tree.routes.common import bp as common_bp
    app.register_blueprint(common_bp)
    from family_tree.routes.user import bp as user_bp
    app.register_blueprint(user_bp)
    from family_tree.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    return app

def init_logging(app):
    # Only configure logging if not already configured
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/family_tree.log', maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        
        app.logger.propagate = False
        
        app.logger.info('Family Tree startup')