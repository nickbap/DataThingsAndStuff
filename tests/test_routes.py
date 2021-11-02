import unittest
from datetime import datetime

from dtns import create_app
from dtns import db
from dtns.constants import PostStatus
from dtns.models import Post
from dtns.utils import md


class BaseRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # Create posts
        self.posts = []
        for i in range(1, 6):
            source = f"# Post {i}"
            post = Post(
                title=f"Title {i}",
                slug=f"slug-{i}",
                description=f"Post description {i}",
                source=source,
                html=md.render(source),
            )
            self.posts.append(post)

        db.session.add_all(self.posts)
        db.session.commit()

        # Publish posts
        posts = Post.query.all()
        self.published_posts = []
        for post in posts[:3]:
            now = datetime.utcnow()
            post.state = PostStatus.PUBLISHED
            post.updated_at = now
            post.published_at = now
            self.published_posts.append(post)

        db.session.add_all(self.published_posts)
        db.session.commit()

    def tearDown(self):
        db.drop_all()
        self.app_context.pop()


class NonAdminRouteTestCase(BaseRouteTestCase):
    def setUp(self):
        super(NonAdminRouteTestCase, self).setUp()

    def test_home_route(self):
        response = self.client.get("/")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Data Things & Stuff", response_text)
        for post in self.published_posts:
            self.assertIn(post.title, response_text)
            self.assertIn(post.slug, response_text)
            self.assertIn(post.description, response_text)

    def test_about_route(self):
        response = self.client.get("/about")

        self.assertEqual(response.status_code, 200)
        self.assertIn("About", response.get_data(as_text=True))

    def test_admin_route(self):
        response = self.client.get("/admin")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Admin", response.get_data(as_text=True))
        self.assertNotIn('id="admin-nav"', response_text)
        self.assertIn("Login", response_text)

    def test_create_route(self):
        response = self.client.get("/create")

        self.assertEqual(response.status_code, 401)

    def test_edit_route(self):
        response = self.client.get("/edit/1")

        self.assertEqual(response.status_code, 401)

    def test_publish_route(self):
        response = self.client.post("/publish/1")

        self.assertEqual(response.status_code, 401)

    def test_archive_route(self):
        response = self.client.post("/archive/1")

        self.assertEqual(response.status_code, 401)

    def test_draft_route(self):
        response = self.client.post("/draft/1")

        self.assertEqual(response.status_code, 401)

    def test_preview_route(self):
        response = self.client.get("/preview/slug-1")

        self.assertEqual(response.status_code, 401)

    def test_post_route(self):
        response = self.client.get("/post/slug-1")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Title 1", response_text)
        self.assertIn("slug-1", response_text)
