from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from config import config

toolbar = DebugToolbarExtension()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    toolbar.init_app(app)

    from dtns.routes import main

    app.register_blueprint(main)

    return app
