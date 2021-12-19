from flask import Blueprint
from flask import render_template

error = Blueprint("error", __name__)


@error.app_errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@error.app_errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@error.app_errorhandler(500)
def internal_service_error(error):
    return render_template("errors/500.html"), 500
