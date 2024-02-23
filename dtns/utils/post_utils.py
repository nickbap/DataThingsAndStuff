from datetime import datetime

from flask import current_app
from flask import url_for
from itsdangerous.url_safe import URLSafeTimedSerializer

TEMP_PREVIEW_MAX_AGE = 30 * 60


class TokenType:
    TEMP_PREVIEW = "temp-preview"
    TOGGLE_COMMENT = "toggle-comment"


TOKEN_TYPE_TO_MAX_AGE_MAP = {TokenType.TEMP_PREVIEW: TEMP_PREVIEW_MAX_AGE}


def aggregate_and_sort_posts_by_month_year(posts):
    archive_posts = list({post.published_at.strftime("%B %Y") for post in posts})
    return sorted(
        archive_posts,
        key=lambda post: datetime.strptime(post, "%B %Y"),
        reverse=True,
    )


def generate_temp_token(obj):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(obj)


def generate_temp_preview_url(post):
    token = generate_temp_token(post.slug)
    return url_for("main.temp_preview", preview_id=token, _external=True)


def generate_toggle_comment_url(comment):
    token = generate_temp_token(comment.id)
    return url_for(
        "main.admin_comment_toggle_visibility_state_link",
        token=token,
        _external=True,
    )


def validate_token(token, token_type):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    max_age = TOKEN_TYPE_TO_MAX_AGE_MAP.get(token_type)
    return s.loads(token, max_age=max_age)
