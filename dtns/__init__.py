from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from config import config

toolbar = DebugToolbarExtension()


def create_app(testing_config=None):
    app = Flask(__name__)

    if testing_config is None:
        app.config.from_object(config["config"])
    else:
        app.config.from_object(config["testing"])

    toolbar.init_app(app)

    from dtns.routes import main

    app.register_blueprint(main)

    return app
