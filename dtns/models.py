from datetime import datetime

from dtns import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<User {self.id} {self.username}>"
