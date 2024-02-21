import os
from datetime import date

from flask import Blueprint
from flask import abort
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_login.utils import login_required
from itsdangerous import SignatureExpired
from werkzeug.security import check_password_hash

from dtns import db
from dtns.constants import POST_STATUS_STYLE
from dtns.constants import PostStatus
from dtns.forms import BlogPostForm
from dtns.forms import CommentForm
from dtns.forms import ImageUploadForm
from dtns.forms import LoginForm
from dtns.model_storage import CommentModelStorage
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
    post = PostModelStorage.get_post_by_slug("about")
    return render_template("about.html", post=post)


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
    return render_template(
        "admin/home.html", form=form, posts=posts, POST_STATUS_STYLE=POST_STATUS_STYLE
    )


@main.route("/admin/posts", methods=["GET"])
@login_required
def admin_posts():
    posts = PostModelStorage.get_all_posts_ordered_by_updated_at()
    return render_template(
        "admin/posts.html", posts=posts, POST_STATUS_STYLE=POST_STATUS_STYLE
    )


@main.route("/admin/users", methods=["GET"])
@login_required
def admin_users():
    users = UserModelStorage.get_all_for_admin()
    return render_template("admin/users.html", users=users)


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


@main.route("/temp-preview/<int:post_id>", methods=["POST"])
@login_required
def temp_preview_link(post_id):
    post = PostModelStorage.get(post_id)

    url = post_utils.generate_temp_preview_url(post)

    flash(f"Temporary preview link: \n{url}", "warning")
    return redirect(url_for("main.preview", slug=post.slug))


@main.route("/temp-preview", methods=["GET"])
def temp_preview():
    preview_id = request.args.get("preview_id")
    if not preview_id:
        abort(401)

    try:
        slug = post_utils.validate_temp_preview_token(preview_id)
    except SignatureExpired:
        return render_template("errors/expired-link.html")

    recent_post_list = PostModelStorage.get_recent_posts()
    post = PostModelStorage.get_post_by_slug(slug)

    if not post:
        abort(404)

    return render_template("post.html", recent_post_list=recent_post_list, post=post)


@main.route("/preview/<slug>")
@login_required
def preview(slug):
    recent_post_list = PostModelStorage.get_recent_posts()
    post = PostModelStorage.get_post_by_slug(slug)
    if not post:
        abort(404)
    return render_template("post.html", recent_post_list=recent_post_list, post=post)


@main.route("/post/<slug>", methods=["GET", "POST"])
def post(slug):
    recent_post_list = PostModelStorage.get_recent_posts()
    post = PostModelStorage.get_post_by_slug(slug)
    if not post:
        abort(404)

    form = CommentForm()
    if form.validate_on_submit():
        try:
            data = {
                "email": form.email.data,
                "username": form.username.data,
                "comment": form.comment.data,
                "post": post,
            }
            CommentModelStorage.create_comment(data)
            flash("Your comment has been added!", "success")
            return redirect(url_for("main.post", slug=post.slug))
        except Exception:
            flash("Sorry, something went wrong with adding your comment!", "danger")
            return redirect(url_for("main.post", slug=post.slug))
    return render_template(
        "post.html", recent_post_list=recent_post_list, post=post, slug=slug, form=form
    )


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
    image_manager = image_utils.ImageManager(current_app)
    image_list = image_manager.get_all_images()
    if request.method == "POST":
        file_upload = request.files["file"]
        filename = image_manager.save_image(file_upload)
        if not filename:
            flash(
                "Something went wrong with your upload. Please check and try again.",
                "danger",
            )
            return redirect(url_for("main.image_manager"))
        flash(f'Sucessfully uploaded "{filename}"', "success")
        return redirect(url_for("main.image_manager"))
    return render_template("image-manager.html", form=form, image_list=image_list)


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/health")
def health_check():
    db.engine.execute("SELECT 1")
    return ""
