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


class AdminRouteTestCase(BaseRouteTestCase):
    def setUp(self):
        super(AdminRouteTestCase, self).setUp()
        self.app.config["LOGIN_DISABLED"] = True

        # Archive a post
        post = Post.query.get(5)
        post.state = PostStatus.ARCHIVED
        post.updated_at = datetime.utcnow()
        post.published_at = None

        db.session.add(post)
        db.session.commit()

    def test_create_route(self):
        response = self.client.get("/create")

        self.assertEqual(response.status_code, 200)

    def test_create_post_from_post_route(self):
        post_data = {
            "title": "Post Route Title",
            "slug": "post-route-title",
            "description": "Post route post description",
            "source": "# Post Route Post",
        }
        response = self.client.post("/create", data=post_data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your Post has been created!", response_text)
        self.assertIn("success", response_text)

    def test_edit_post_route(self):
        response = self.client.get("/edit/1")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Post Editor", response_text)
        self.assertIn('id="blog-post-editor"', response_text)
        self.assertIn("Post Preview", response_text)
        self.assertIn('id="blog-home-page-preview"', response_text)
        self.assertIn('id="blog-post-preview"', response_text)

    def test_edit_post_from_edit_route(self):
        updated_post_data = {
            "title": "updated title",
            "slug": "updated-slug",
            "description": "updated description",
            "source": "updated source",
        }
        response = self.client.post(
            "/edit/1", data=updated_post_data, follow_redirects=True
        )
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("updated", response_text)

    def test_preview_page(self):
        response = self.client.get("/preview/slug-1")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Title 1", response_text)
        self.assertIn('id="post-content', response_text)
        self.assertIn("Edit", response_text)
        self.assertIn("Publish", response_text)
        self.assertIn("Archive", response_text)
        self.assertIn("Draft", response_text)

    def test_publish_route(self):
        response = self.client.post("/publish/4", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your post has been published!", response_text)
        self.assertIn("success", response_text)

    def test_publish_post_already_published(self):
        response = self.client.post("/publish/1", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("This post has already been published!", response_text)
        self.assertIn("danger", response_text)

    def test_archive_post(self):
        response = self.client.post("/archive/1", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your post has been archived!", response_text)
        self.assertIn("success", response_text)

    def test_archive_post_already_archived(self):
        response = self.client.post("/archive/5", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("This post has already been archived!", response_text)
        self.assertIn("danger", response_text)

    def test_mark_post_as_draft(self):
        response = self.client.post("/draft/1", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your post has been marked as a draft!", response_text)
        self.assertIn("success", response_text)

    def test_mark_post_as_draft_already_a_draft(self):
        response = self.client.post("/draft/4", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("This post is already a draft!", response_text)
        self.assertIn("danger", response_text)
