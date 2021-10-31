from datetime import date
from datetime import datetime

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
from sqlalchemy import desc
from werkzeug.security import check_password_hash

from dtns import db
from dtns.data import temp_posts
from dtns.forms import BlogPostForm
from dtns.forms import LoginForm
from dtns.models import Post
from dtns.models import User
from dtns.utils import md

main = Blueprint("main", __name__)


@main.route("/")
def index():
    posts = temp_posts
    return render_template("home.html", posts=posts)


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/admin", methods=["GET", "POST"])
def admin():
    if current_user.is_authenticated:
        posts = Post.query.all()
    else:
        posts = None

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
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
        post = Post(
            title=form.title.data,
            slug=form.slug.data,
            description=form.description.data,
            source=form.source.data,
            html=md.render(form.source.data),
        )
        db.session.add(post)
        db.session.commit()

        flash("Your Post has been created!", "success")
        return redirect(url_for("main.admin"))
    return render_template("editor.html", form=form, today=today)


@main.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
    form = BlogPostForm()
    if form.validate_on_submit():
        post = Post.query.get(post_id)

        post.title = form.title.data
        post.slug = form.slug.data
        post.description = form.description.data
        post.source = form.source.data
        post.html = md.render(form.source.data)
        post.updated_at = datetime.utcnow()

        db.session.add(post)
        db.session.commit()

        flash("Your post has been updated!", "success")
        return redirect(url_for("main.admin"))

    post = Post.query.get(post_id)

    form.title.data = post.title
    form.slug.data = post.slug
    form.description.data = post.description
    form.source.data = post.source
    return render_template("editor.html", form=form, post=post, today=date.today())


@main.route("/preview/<slug>")
@login_required
def preview(slug):
    posts = (
        Post.query.order_by(desc("created_at")).limit(5).all()
    )  # should use published_at for prod
    post = Post.query.filter_by(slug=slug).first()
    return render_template("post.html", posts=posts, post=post)


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))
