import unittest
from unittest import mock
from datetime import datetime

from werkzeug.security import generate_password_hash

from dtns import create_app
from dtns import db
from dtns.constants import CommentState
from dtns.constants import PostStatus
from dtns.models import Comment
from dtns.models import Post
from dtns.models import User


class PostModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        self.title = "A Test Title"
        self.slug = "a-test-tile"
        self.description = "A test post description"
        self.source = "# Hey"
        self.html = "<h1>Hey</h1>\n"

        self.username = "test_user"
        self.email = "test@test.com"
        self.password = "test_password"
        self.password_hash = generate_password_hash(self.password)
        self.u = User(
            email=self.email, username=self.username, password=self.password_hash
        )
        db.session.add(self.u)
        db.session.commit()

    def tearDown(self):
        db.session.commit()
        db.drop_all()
        self.app_context.pop()

    def test_create_post(self):
        p = Post(
            title=self.title,
            slug=self.slug,
            description=self.description,
            source=self.source,
        )
        db.session.add(p)
        db.session.commit()

        post = Post.query.first()

        self.assertEqual(self.title, post.title)
        self.assertEqual(self.slug, post.slug)
        self.assertEqual(self.description, post.description)
        self.assertEqual(self.source, post.source)
        self.assertEqual(self.html, post.html)
        self.assertIn(self.slug, str(post))

    def test_create_post_is_draft_by_default(self):
        p = Post(
            title=self.title,
            slug=self.slug,
            description=self.description,
            source=self.source,
        )
        db.session.add(p)
        db.session.commit()

        post = Post.query.first()

        self.assertEqual(PostStatus.DRAFT, post.state)

    def test_create_post_publised_at_is_none_by_default(self):
        p = Post(
            title=self.title,
            slug=self.slug,
            description=self.description,
            source=self.source,
        )
        db.session.add(p)
        db.session.commit()

        post = Post.query.first()

        self.assertIsNone(post.published_at)

    def test_create_post_created_at_updated_at_is_recorded(self):
        p = Post(
            title=self.title,
            slug=self.slug,
            description=self.description,
            source=self.source,
        )
        db.session.add(p)
        db.session.commit()

        post = Post.query.first()

        self.assertIsInstance(post.created_at, datetime)
        self.assertIsInstance(post.updated_at, datetime)


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.email = "test@test.com"
        self.username = "test_user"
        self.password = "test_password"

    def tearDown(self):
        db.session.commit()
        db.drop_all()
        self.app_context.pop()

    def test_create_user(self):
        user = User(email=self.email, username=self.username, password=self.password)

        db.session.add(user)
        db.session.commit()
        u = User.query.first()

        self.assertIsNotNone(u)
        self.assertEqual(self.email, u.email)
        self.assertEqual(self.username, u.username)
        self.assertEqual(self.password, u.password)
        self.assertIn(self.username, str(u))

    def test_create_user_is_not_admin_by_default(self):
        user = User(email=self.email, username=self.username, password=self.password)

        db.session.add(user)
        db.session.commit()
        u = User.query.first()

        self.assertFalse(u.is_admin)

    def test_create_user_created_at_is_recorded(self):
        user = User(email=self.email, username=self.username, password=self.password)

        db.session.add(user)
        db.session.commit()
        u = User.query.first()

        self.assertIsNotNone(u.created_at)
        self.assertIsInstance(u.created_at, datetime)


class CommentModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        self.title = "A Test Title"
        self.slug = "a-test-tile"
        self.description = "A test post description"
        self.source = "# Hey"
        self.html = "<h1>Hey</h1>\n"
        self.post = Post(
            title=self.title,
            slug=self.slug,
            description=self.description,
            source=self.source,
        )

        self.username = "test_user"
        self.email = "test@test.com"
        self.password = "test_password"
        self.password_hash = generate_password_hash(self.password)
        self.user = User(
            email=self.email, username=self.username, password=self.password_hash
        )
        db.session.add_all([self.post, self.user])
        db.session.commit()

    def tearDown(self):
        db.session.commit()
        db.drop_all()
        self.app_context.pop()

    @mock.patch("dtns.utils.post_utils.validate_comment_text", new=mock.Mock())
    def test_create_comment(self):
        c = Comment(text="My first test comment", user=self.user, post=self.post)
        db.session.add(c)
        db.session.commit()

        comment = Comment.query.first()

        self.assertIsNotNone(comment)
        self.assertIsInstance(comment.created_at, datetime)
        self.assertEqual("My first test comment", comment.text)
        self.assertEqual(CommentState.VISIBLE, comment.state)
        self.assertEqual(self.post, comment.post)
        self.assertEqual(self.user, comment.user)

    def test_create_comment_is_visible_by_default(self):
        c = Comment(text="My first test comment", user=self.user, post=self.post)
        db.session.add(c)
        db.session.commit()

        comment = Comment.query.first()

        self.assertEqual(CommentState.VISIBLE, comment.state)
