from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
toolbar = DebugToolbarExtension()


def create_app(testing_config=None):
    app = Flask(__name__)

    if testing_config is None:
        app.config.from_object(config["config"])
    else:
        app.config.from_object(config["testing"])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    toolbar.init_app(app)

    from dtns.routes import main

    app.register_blueprint(main)

    from dtns import models

    return app
