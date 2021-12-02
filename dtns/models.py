from datetime import datetime

from flask_login import UserMixin

from dtns import db
from dtns import login_manager
from dtns.constants import PostStatus
from dtns.utils.render_utils import md


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)
    title = db.Column(db.String(256), nullable=False)
    slug = db.Column(db.String(256), index=True, nullable=False)
    description = db.Column(db.Text)
    state = db.Column(db.String(30), default=PostStatus.DRAFT)
    source = db.Column(db.Text)
    html = db.Column(db.Text)

    def generate_html(self, source):
        self.html = md.render(source)

    @staticmethod
    def on_change_source(target, value, oldvalue, initiator):
        return target.generate_html(value)

    def __repr__(self):
        return f"<Post {self.id} {self.slug}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<User {self.id} {self.username}>"


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


db.event.listen(Post.source, "set", Post.on_change_source)
