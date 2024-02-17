from datetime import datetime

from flask import current_app
from flask import url_for
from itsdangerous.url_safe import URLSafeTimedSerializer

MAX_AGE = 30 * 60

alert_template = """
    <div class="py-2">
        <div id="alerts" class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button id="alert-button" type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"
            hx-trigger="click, keyup[Escape] from:body"></button>
        </div>
    </div>
    """


def aggregate_and_sort_posts_by_month_year(posts):
    archive_posts = list({post.published_at.strftime("%B %Y") for post in posts})
    return sorted(
        archive_posts,
        key=lambda post: datetime.strptime(post, "%B %Y"),
        reverse=True,
    )


def generate_temp_preview_token(slug):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(slug)


def generate_temp_preview_url(post):
    token = generate_temp_preview_token(post.slug)
    return url_for("main.temp_preview", preview_id=token, _external=True)


def validate_temp_preview_token(preview_id):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.loads(preview_id, max_age=MAX_AGE)
