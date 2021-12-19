import os
from datetime import date
from urllib.parse import unquote

from flask import Blueprint
from flask import abort
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import render_template_string
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_login.utils import login_required
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from dtns import db
from dtns.constants import PostStatus
from dtns.forms import BlogPostForm
from dtns.forms import ImageUploadForm
from dtns.forms import LoginForm
from dtns.model_storage import PostModelStorage
from dtns.model_storage import UserModelStorage
from dtns.utils import image_utils
from dtns.utils import post_utils

main = Blueprint("main", __name__)


@main.route("/")
def index():
    recent_post_list = PostModelStorage.get_recent_posts()
    posts = PostModelStorage.get_all_published_posts()
    post_archive = post_utils.aggregate_and_sort_posts_by_month_year(posts)
    return render_template(
        "home.html",
        recent_post_list=recent_post_list,
        posts=posts,
        post_archive=post_archive,
    )


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/admin", methods=["GET", "POST"])
def admin():
    if current_user.is_authenticated:
        posts = PostModelStorage.get_all_posts_ordered_by_updated_at()
    else:
        posts = None

    form = LoginForm()
    if form.validate_on_submit():
        user = UserModelStorage.get_user_by_email(form.email.data)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            flash("Welcome to Data Things and Stuff!", "success")
            return (
                redirect(next_page)
                if next_page and next_page.startswith("/")
                else redirect(url_for("main.admin"))
            )
        else:
            flash("Something went wrong with your login! Please try again.", "danger")
    return render_template("admin.html", form=form, posts=posts)


@main.route("/create", methods=["GET", "POST"])
@login_required
def create():
    today = date.today()
    form = BlogPostForm()
    if form.validate_on_submit():
        data = {
            "title": form.title.data,
            "slug": form.slug.data,
            "description": form.description.data,
            "source": form.source.data,
        }
        PostModelStorage.create_post(data)

        flash("Your Post has been created!", "success")
        return redirect(url_for("main.admin"))
    return render_template("editor.html", form=form, today=today)


@main.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
    form = BlogPostForm()
    post = PostModelStorage.get(post_id)

    if form.validate_on_submit():
        data = {
            "title": form.title.data,
            "slug": form.slug.data,
            "description": form.description.data,
            "source": form.source.data,
        }

        PostModelStorage.edit_post(post.id, data)

        flash("Your post has been updated!", "success")
        return redirect(url_for("main.admin"))

    form.title.data = post.title
    form.slug.data = post.slug
    form.description.data = post.description
    form.source.data = post.source
    return render_template("editor.html", form=form, post=post, today=date.today())


@main.route("/publish/<int:post_id>", methods=["POST"])
@login_required
def publish(post_id):
    post = PostModelStorage.get(post_id)

    if post.state == PostStatus.PUBLISHED:
        flash("This post has already been published!", "danger")
        return redirect(url_for("main.admin"))

    PostModelStorage.publish_post(post.id)

    flash("Your post has been published!", "success")
    return redirect(url_for("main.admin"))


@main.route("/archive/<int:post_id>", methods=["POST"])
@login_required
def archive(post_id):
    post = PostModelStorage.get(post_id)

    if post.state == PostStatus.ARCHIVED:
        flash("This post has already been archived!", "danger")
        return redirect(url_for("main.admin"))

    PostModelStorage.archive_post(post.id)

    flash("Your post has been archived!", "success")
    return redirect(url_for("main.admin"))


@main.route("/draft/<int:post_id>", methods=["POST"])
@login_required
def draft(post_id):
    post = PostModelStorage.get(post_id)

    if post.state == PostStatus.DRAFT:
        flash("This post is already a draft!", "danger")
        return redirect(url_for("main.admin"))

    PostModelStorage.mark_post_as_draft(post.id)

    flash("Your post has been marked as a draft!", "success")
    return redirect(url_for("main.admin"))


@main.route("/preview/<slug>")
@login_required
def preview(slug):
    recent_post_list = PostModelStorage.get_recent_posts()
    post = PostModelStorage.get_post_by_slug(slug)
    if not post:
        abort(404)
    return render_template("post.html", recent_post_list=recent_post_list, post=post)


@main.route("/post/<slug>")
def post(slug):
    recent_post_list = PostModelStorage.get_recent_posts()
    post = PostModelStorage.get_post_by_slug(slug)
    if not post:
        abort(404)
    return render_template("post.html", recent_post_list=recent_post_list, post=post)


@main.route("/uploads/<name>")
def download_file(name):
    upload_folder_path = os.path.join(
        current_app.static_folder, current_app.config["UPLOAD_FOLDER"]
    )
    return send_from_directory(upload_folder_path, name)


@main.route("/image-manager", methods=["GET", "POST"])
@login_required
def image_manager():
    form = ImageUploadForm()
    image_list = [
        image
        for image in os.listdir(
            os.path.join(current_app.static_folder, current_app.config["UPLOAD_FOLDER"])
        )
        if image_utils.is_valid_image_type(image)
    ]
    if request.method == "POST":
        file_upload = request.files["file"]
        filename = secure_filename(file_upload.filename)
        if not image_utils.is_valid_image(filename):
            flash(
                "Something went wrong with your upload. Please check and try again.",
                "danger",
            )
            return redirect(url_for("main.image_manager"))

        file_upload.save(
            os.path.join(
                current_app.static_folder,
                current_app.config["UPLOAD_FOLDER"],
                filename,
            ),
        )
        flash(f'Sucessfully uploaded "{filename}"', "success")
        return redirect(url_for("main.image_manager"))
    return render_template("image-manager.html", form=form, image_list=image_list)


@main.route("/search", methods=["POST"])
def search_posts():
    search_terms = request.form["search"]
    posts = PostModelStorage.search_posts(search_terms)
    posts_template = """
    <div class="text-center pb-1">
        <span>Results for: "{{ search_terms }}" <a class="text-reset" href="{{ url_for('main.index') }}"><i
                    class="bi bi-x"></i></a></span>
    </div>
    {% for post in posts %}
        <div class="border p-4 mb-2 shadow-sm">
            <h3 class="mb-0">{{ post.title }}</h3>
            <p class="mb-1 text-muted">{{ post.published_at.strftime('%B %-d, %Y') }}</p>
            <p class="card-text mb-auto">{{ post.description }}</p>
            <a href="{{ url_for('main.post', slug=post.slug) }}">Continue reading</a>
        </div>
    {% endfor %}
    """
    return render_template_string(
        posts_template, search_terms=search_terms, posts=posts
    )


@main.route("/posts/<month_year>")
def posts_month_year(month_year):
    posts = PostModelStorage.get_posts_by_month_year(unquote(month_year))
    posts_template = """
    <div class="text-center pb-1">
        <span>Results for: "{{ month_year }}" <a class="text-reset" href="{{ url_for('main.index') }}"><i
                    class="bi bi-x"></i></a></span>
    </div>
    {% for post in posts %}
        <div class="border p-4 mb-2 shadow-sm">
            <h3 class="mb-0">{{ post.title }}</h3>
            <p class="mb-1 text-muted">{{ post.published_at.strftime('%B %-d, %Y') }}</p>
            <p class="card-text mb-auto">{{ post.description }}</p>
            <a href="{{ url_for('main.post', slug=post.slug) }}">Continue reading</a>
        </div>
    {% endfor %}
    """
    return render_template_string(posts_template, month_year=month_year, posts=posts)


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/health")
def health_check():
    db.engine.execute("SELECT 1")
    return ""
