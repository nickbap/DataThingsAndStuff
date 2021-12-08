import io
import os
import unittest
from datetime import datetime
from urllib.parse import quote

from PIL import Image
from PIL import ImageDraw

from dtns import create_app
from dtns import db
from dtns.constants import PostStatus
from dtns.models import Post


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

        self.full_upload_path = os.path.join(
            self.app.static_folder, self.app.config["UPLOAD_FOLDER"]
        )
        self.filename = "image-from-test.jpeg"

    def tearDown(self):
        test_file_path = os.path.join(self.full_upload_path, self.filename)
        if os.path.isfile(test_file_path):
            os.remove(test_file_path)

        db.session.commit()
        db.drop_all()
        self.app_context.pop()


class RoutesAsUserTestCase(BaseRouteTestCase):
    def setUp(self):
        super(RoutesAsUserTestCase, self).setUp()

    def test_home_route_as_user(self):
        response = self.client.get("/")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Data Things & Stuff", response_text)
        self.assertIn("Search", response_text)
        self.assertIn("Archive", response_text)
        for post in self.published_posts:
            self.assertIn(post.title, response_text)
            self.assertIn(post.slug, response_text)
            self.assertIn(post.description, response_text)

    def test_about_route_as_user(self):
        response = self.client.get("/about")

        self.assertEqual(response.status_code, 200)
        self.assertIn("About", response.get_data(as_text=True))

    def test_admin_route_as_user(self):
        response = self.client.get("/admin")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Admin", response.get_data(as_text=True))
        self.assertNotIn('id="admin-nav"', response_text)
        self.assertIn("Login", response_text)

    def test_create_route_as_user(self):
        response = self.client.get("/create")

        self.assertEqual(response.status_code, 401)

    def test_edit_route_as_user(self):
        response = self.client.get("/edit/1")

        self.assertEqual(response.status_code, 401)

    def test_publish_route_as_user(self):
        response = self.client.post("/publish/1")

        self.assertEqual(response.status_code, 401)

    def test_archive_route_as_user(self):
        response = self.client.post("/archive/1")

        self.assertEqual(response.status_code, 401)

    def test_draft_route_as_user(self):
        response = self.client.post("/draft/1")

        self.assertEqual(response.status_code, 401)

    def test_preview_route_as_user(self):
        response = self.client.get("/preview/slug-1")

        self.assertEqual(response.status_code, 401)

    def test_post_route_as_user(self):
        response = self.client.get("/post/slug-1")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Title 1", response_text)
        self.assertIn("slug-1", response_text)

    def test_image_manager_route_as_user(self):
        response = self.client.get("/image-manager")

        self.assertEqual(response.status_code, 401)

    def test_upload_image_as_user(self):
        data = {}
        data["file"] = (io.BytesIO(b"abcdef"), self.filename)

        response = self.client.post("/image-manager", data=data, follow_redirects=True)

        self.assertEqual(response.status_code, 401)

    def test_health_check_as_user(self):
        response = self.client.get("/health")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_text, "")

    def test_search(self):
        # create post to find
        post = Post(
            title="New Fake Title To Find",
            slug="new-fake-title-to-find",
            description="Post description",
            source="Here's a post. Find me later!",
        )
        db.session.add(post)
        db.session.commit()

        # publish the new post
        post = Post.query.filter_by(title="New Fake Title To Find").first()

        now = datetime.utcnow()
        post.state = PostStatus.PUBLISHED
        post.updated_at = now
        post.published_at = now

        db.session.add(post)
        db.session.commit()

        search_data = {"search": "find"}
        response = self.client.post("/search", data=search_data)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("New Fake Title To Find", response_text)
        self.assertIn('Results for: "find"', response_text)

    def test_post_archive(self):
        today = datetime.utcnow().strftime("%B %Y")
        url = f"/posts/{quote(today)}"

        response = self.client.get(url)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(f'Results for: "{today}"', response_text)


class RoutesAsAdminTestCase(BaseRouteTestCase):
    def setUp(self):
        super(RoutesAsAdminTestCase, self).setUp()
        self.app.config["LOGIN_DISABLED"] = True

        # Archive a post
        post = Post.query.get(5)
        post.state = PostStatus.ARCHIVED
        post.updated_at = datetime.utcnow()
        post.published_at = None

        db.session.add(post)
        db.session.commit()

    def test_create_route_as_admin(self):
        response = self.client.get("/create")

        self.assertEqual(response.status_code, 200)

    def test_create_post_from_post_route_as_admin(self):
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

    def test_edit_post_route_as_admin(self):
        response = self.client.get("/edit/1")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Post Editor", response_text)
        self.assertIn('id="blog-post-editor"', response_text)
        self.assertIn("Post Preview", response_text)
        self.assertIn('id="blog-home-page-preview"', response_text)
        self.assertIn('id="blog-post-preview"', response_text)

    def test_edit_post_from_edit_route_as_admin(self):
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

    def test_preview_page_as_admin(self):
        response = self.client.get("/preview/slug-1")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Title 1", response_text)
        self.assertIn('id="post-content', response_text)
        self.assertIn("Edit", response_text)
        self.assertIn("Publish", response_text)
        self.assertIn("Archive", response_text)
        self.assertIn("Draft", response_text)

    def test_publish_route_as_admin(self):
        response = self.client.post("/publish/4", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your post has been published!", response_text)
        self.assertIn("success", response_text)

    def test_publish_post_already_published_as_admin(self):
        response = self.client.post("/publish/1", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("This post has already been published!", response_text)
        self.assertIn("danger", response_text)

    def test_archive_post_as_admin(self):
        response = self.client.post("/archive/1", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your post has been archived!", response_text)
        self.assertIn("success", response_text)

    def test_archive_post_already_archived_as_admin(self):
        response = self.client.post("/archive/5", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("This post has already been archived!", response_text)
        self.assertIn("danger", response_text)

    def test_mark_post_as_draft_as_admin(self):
        response = self.client.post("/draft/1", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your post has been marked as a draft!", response_text)
        self.assertIn("success", response_text)

    def test_mark_post_as_draft_already_a_draft_as_admin(self):
        response = self.client.post("/draft/4", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("This post is already a draft!", response_text)
        self.assertIn("danger", response_text)

    def test_image_manager_route_as_admin(self):
        response = self.client.get("/image-manager")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Image Manager", response_text)

    def test_upload_image_as_admin(self):
        data = {}
        data["file"] = (io.BytesIO(b"abcdef"), self.filename)

        response = self.client.post("/image-manager", data=data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.filename, response_text)
        self.assertIn("success", response_text)

    def test_upload_image_failure_as_admin(self):
        data = {}
        data["file"] = (io.BytesIO(b"abcdef"), "test-image.tiff")

        response = self.client.post("/image-manager", data=data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("test-image.tiff", response_text)
        self.assertIn("danger", response_text)


def create_test_image():
    img = Image.new(mode="RGB", size=(200, 200))
    ImageDraw.Draw(img).text((100, 100), "Testing... 1,2,3", (255, 255, 255))
    return img


class ServeUploadTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.full_upload_path = os.path.join(
            self.app.static_folder, self.app.config["UPLOAD_FOLDER"]
        )
        self.filename = "image-from-test.jpeg"

        img = create_test_image()
        img.save(os.path.join(self.full_upload_path, self.filename))

    def tearDown(self):
        self.app_context.pop()

        os.remove(os.path.join(self.full_upload_path, self.filename))

    def test_serve_upload(self):
        response = self.client.get(f"/uploads/{self.filename}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/jpeg")
