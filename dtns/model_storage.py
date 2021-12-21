from datetime import datetime

from sqlalchemy import desc
from sqlalchemy import func

from dtns import db
from dtns.constants import PostStatus
from dtns.models import Post
from dtns.models import User


class BaseModelStorage:
    @classmethod
    def get(cls, id):
        return cls.model.query.get(id)

    @classmethod
    def get_first(cls):
        return cls.model.query.first()

    @classmethod
    def get_all(cls):
        return cls.model.query.all()

    @classmethod
    def filter_(cls, **kwargs):
        return cls.model.query.filter_by(**kwargs).all()


class PostModelStorage(BaseModelStorage):
    model = Post

    @classmethod
    def get_all_published_posts(cls):
        """
        Return all published posts ordered by published date.
        """
        return (
            cls.model.query.filter_by(state=PostStatus.PUBLISHED)
            .order_by(desc("published_at"))
            .all()
        )

    @classmethod
    def get_recent_posts(cls):
        """
        Return 5 most recent published posts ordered by published date.
        """
        return (
            cls.model.query.filter_by(state=PostStatus.PUBLISHED)
            .order_by(desc("published_at"))
            .limit(5)
            .all()
        )

    @classmethod
    def get_all_posts_ordered_by_updated_at(cls):
        return cls.model.query.order_by(desc("updated_at")).all()

    @classmethod
    def get_post_by_slug(cls, slug):
        post = cls.filter_(slug=slug)
        if not post:
            return
        return post[0]

    @classmethod
    def create_post(cls, data):
        post = Post(
            title=data["title"],
            slug=data["slug"],
            description=data["description"],
            source=data["source"],
        )
        db.session.add(post)
        db.session.commit()

    @classmethod
    def edit_post(cls, post_id, data):
        post = cls.get(id=post_id)

        post.title = data["title"] if data["title"] != post.title else post.title
        post.slug = data["slug"] if data["slug"] != post.slug else post.slug
        post.description = (
            data["description"]
            if data["description"] != post.description
            else post.description
        )
        post.source = data["source"] if data["source"] != post.source else post.source
        post.updated_at = datetime.utcnow()

        db.session.add(post)
        db.session.commit()

    @classmethod
    def publish_post(cls, post_id):
        post = cls.get(id=post_id)

        now = datetime.utcnow()
        post.state = PostStatus.PUBLISHED
        post.updated_at = now
        post.published_at = now

        db.session.add(post)
        db.session.commit()

    @classmethod
    def archive_post(cls, post_id):
        post = cls.get(id=post_id)

        post.state = PostStatus.ARCHIVED
        post.updated_at = datetime.utcnow()
        post.published_at = None

        db.session.add(post)
        db.session.commit()

    @classmethod
    def mark_post_as_draft(cls, post_id):
        post = cls.get(id=post_id)

        post.state = PostStatus.DRAFT
        post.updated_at = datetime.utcnow()
        post.published_at = None

        db.session.add(post)
        db.session.commit()

    @classmethod
    def search_posts(cls, search_terms):
        """
        Return published posts with source containing given search terms
        """
        return cls.model.query.filter(
            func.lower(Post.source).like(f"%{search_terms.lower()}%"),
            Post.state == PostStatus.PUBLISHED,
        ).all()

    @classmethod
    def get_posts_by_month_year(cls, month_year):
        return cls.model.query.filter(
            (func.date_format(Post.published_at, "%M %Y") == month_year)
        ).all()


class UserModelStorage(BaseModelStorage):
    model = User

    @classmethod
    def get_user_by_email(cls, email):
        if not email:
            return

        user = cls.filter_(email=email.lower())

        if not user:
            return

        return user[0]
