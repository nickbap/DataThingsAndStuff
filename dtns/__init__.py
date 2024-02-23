import sentry_sdk
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration

from config import config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
toolbar = DebugToolbarExtension()


def create_app(testing_config=None):
    app = Flask(__name__)

    if testing_config is None:
        app.config.from_object(config["config"])

        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
        )
    else:
        app.config.from_object(config["testing"])

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    toolbar.init_app(app)

    from dtns.routes import main

    app.register_blueprint(main)

    from dtns.errors import error

    app.register_blueprint(error)

    from dtns.ajax import ajax

    app.register_blueprint(ajax)

    from dtns import models  # noqa: F401

    if app.debug:
        from dtns import model_storage  # noqa: F401

        @app.shell_context_processor
        def make_shell_context():
            return {
                "db": db,
                "Comment": models.Comment,
                "CommentModelStorage": model_storage.CommentModelStorage,
                "Post": models.Post,
                "PostModelStorage": model_storage.PostModelStorage,
                "User": models.User,
                "UserModelStorage": model_storage.UserModelStorage,
            }

    return app
