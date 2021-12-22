from datetime import datetime
from urllib.parse import unquote

from flask import Blueprint
from flask import current_app
from flask import render_template_string
from flask import request

from dtns.model_storage import PostModelStorage
from dtns.utils import image_utils
from dtns.utils import post_utils

ajax = Blueprint("ajax", __name__)


@ajax.route("/search", methods=["POST"])
def search_posts():
    search_terms = request.form["search"]
    posts = PostModelStorage.search_posts(search_terms)
    return render_template_string(
        post_utils.post_list_template, criteria=search_terms, posts=posts
    )


@ajax.route("/posts/<month_year>")
def posts_month_year(month_year):
    posts = PostModelStorage.get_posts_by_month_year(unquote(month_year))
    return render_template_string(
        post_utils.post_list_template, criteria=month_year, posts=posts
    )


@ajax.route("/save/<post_id>", methods=["POST"])
def save_post(post_id):
    data = {
        "title": request.form["title"],
        "slug": request.form["slug"],
        "description": request.form["description"],
        "source": request.form["source"],
    }

    PostModelStorage.edit_post(post_id, data)

    return render_template_string(
        post_utils.alert_template,
        category="success",
        message=f"Saved at { datetime.utcnow().strftime('%H:%M:%S') }!",
    )


@ajax.route("/image-manager/sort")
def sort_image_manager_images():
    option = bool(int(request.args["asc"]))
    image_manager = image_utils.ImageManager(current_app)
    image_list = image_manager.get_all_images_sorted(asc=option)
    return render_template_string(
        image_utils.image_list_template, image_list=image_list
    )
