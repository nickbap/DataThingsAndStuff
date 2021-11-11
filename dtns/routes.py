from datetime import date

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_login.utils import login_required
from werkzeug.security import check_password_hash

from dtns.constants import PostStatus
from dtns.forms import BlogPostForm
from dtns.forms import LoginForm
from dtns.model_storage import PostModelStorage
from dtns.model_storage import UserModelStorage

main = Blueprint("main", __name__)


@main.route("/")
def index():
    posts = PostModelStorage.get_all_published_posts()
    post_list = PostModelStorage.get_recent_posts()
    return render_template("home.html", posts=posts, post_list=post_list)


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
            "description": form.slug.data,
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
            "description": form.slug.data,
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
    # TODO rename posts to post_list
    posts = PostModelStorage.get_recent_posts()
    post = PostModelStorage.get_post_by_slug(slug)
    return render_template("post.html", posts=posts, post=post)


@main.route("/post/<slug>")
def post(slug):
    # TODO rename posts to post_list
    posts = PostModelStorage.get_recent_posts()
    post = PostModelStorage.get_post_by_slug(slug)
    return render_template("post.html", posts=posts, post=post)


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))
