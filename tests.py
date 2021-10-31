import unittest
from datetime import datetime

from flask import current_app
from werkzeug.security import generate_password_hash

from dtns import create_app
from dtns import db
from dtns.constants import PostStatus
from dtns.models import Post
from dtns.models import User


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_app_testing_config(self):
        self.assertFalse(current_app.config["DEBUG"])
        self.assertTrue(current_app.config["TESTING"])

    @unittest.skip  # need to handle the posts from db better
    def test_home_route(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Data Things & Stuff", response.get_data(as_text=True))

    def test_about_route(self):
        response = self.client.get("/about")

        self.assertEqual(response.status_code, 200)
        self.assertIn("About", response.get_data(as_text=True))

    def test_admin_route(self):
        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Admin", response.get_data(as_text=True))


class TestAppConfig(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_app_config(self):
        self.assertFalse(current_app.config["DEBUG"])
        self.assertFalse(current_app.config["TESTING"])
        self.assertEqual(current_app.config["ENV"], "production")


class TestPostModel(unittest.TestCase):
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
        self.html = "<h1>Hey</h1>"

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
        db.drop_all()
        self.app_context.pop()

    def test_create_post(self):
        p = Post(
            title=self.title,
            slug=self.slug,
            description=self.description,
            source=self.source,
            html=self.html,
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
            html=self.html,
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
            html=self.html,
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
            html=self.html,
        )
        db.session.add(p)
        db.session.commit()

        post = Post.query.first()

        self.assertTrue(isinstance(post.created_at, datetime))
        self.assertTrue(isinstance(post.updated_at, datetime))

    def test_create_post_from_editor(self):
        user_data = {"email": self.email, "password": self.password}
        response = self.client.post("/admin", data=user_data, follow_redirects=True)

        post_data = {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "source": self.source,
        }
        response = self.client.post("/create", data=post_data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response_text)

        post = Post.query.all()

        self.assertIsNotNone(post)
        self.assertEqual(len(post), 1)
        self.assertEqual(self.title, post[0].title)

    def test_edit_post_page(self):
        user_data = {"email": self.email, "password": self.password}
        self.client.post("/admin", data=user_data, follow_redirects=True)
        post_data = {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "source": self.source,
        }
        self.client.post("/create", data=post_data, follow_redirects=True)

        response = self.client.get("/edit/1")

        self.assertEqual(response.status_code, 200)

    def test_edit_post_from_editor(self):
        user_data = {"email": self.email, "password": self.password}
        self.client.post("/admin", data=user_data, follow_redirects=True)
        post_data = {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "source": self.source,
        }
        self.client.post("/create", data=post_data, follow_redirects=True)

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
        post = Post.query.first()

        self.assertEqual(response.status_code, 200)
        self.assertIn("updated", response_text)
        self.assertEqual(updated_post_data["title"], post.title)
        self.assertEqual(updated_post_data["slug"], post.slug)
        self.assertEqual(updated_post_data["description"], post.description)
        self.assertEqual(updated_post_data["source"], post.source)

    def test_preview_page(self):
        user_data = {"email": self.email, "password": self.password}
        self.client.post("/admin", data=user_data, follow_redirects=True)
        post_data = {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "source": self.source,
        }
        self.client.post("/create", data=post_data, follow_redirects=True)

        response = self.client.get(f"/preview/{self.slug}")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.title, response_text)

    def test_publish_post(self):
        user_data = {"email": self.email, "password": self.password}
        self.client.post("/admin", data=user_data, follow_redirects=True)
        post_data = {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "source": self.source,
        }
        self.client.post("/create", data=post_data, follow_redirects=True)

        response = self.client.post("/publish/1", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your post has been published!", response_text)
        self.assertIn("success", response_text)

        post = Post.query.first()

        self.assertEqual(PostStatus.PUBLISHED, post.state)

    def test_publish_post_already_published(self):
        user_data = {"email": self.email, "password": self.password}
        self.client.post("/admin", data=user_data, follow_redirects=True)
        post_data = {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "source": self.source,
        }
        self.client.post("/create", data=post_data, follow_redirects=True)
        self.client.post("/publish/1", follow_redirects=True)

        response = self.client.post("/publish/1", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("This post has already been published!", response_text)
        self.assertIn("danger", response_text)


class TestUserModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.email = "test@test.com"
        self.username = "test_user"
        self.password = "test_password"

    def tearDown(self):
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
        self.assertTrue(isinstance(u.created_at, datetime))


class TestAppAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        self.email = "test@test.com"
        self.username = "test_user"
        self.password = "test_password"
        self.password_hash = generate_password_hash(self.password)

        self.user = User(
            email=self.email, username=self.username, password=self.password_hash
        )

        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.drop_all()
        self.app_context.pop()

    def test_admin_page_for_unautheticated_user(self):
        response = self.client.get("/admin")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="admin-nav"', response_text)
        self.assertIn("Login", response_text)
        self.assertNotIn(self.username, response_text)
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)

    def test_successful_admin_login(self):
        data = {"email": self.email, "password": self.password}

        response = self.client.post("/admin", data=data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="admin-nav"', response_text)
        self.assertIn("Welcome to Data Things and Stuff!", response_text)
        self.assertIn("success", response_text)
        self.assertIn("New Post", response_text)
        self.assertIn('id="post-list"', response_text)

    def test_unsuccessful_admin_login(self):
        data = {"email": self.email, "password": "aWrongPassWord"}

        response = self.client.post("/admin", data=data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Something went wrong with your login! Please try again.", response_text
        )
        self.assertIn("danger", response_text)
        self.assertNotIn('id="admin-nav"', response_text)
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)

    def test_admin_page_for_autheticated_user(self):
        data = {"email": self.email, "password": self.password}
        self.client.post("/admin", data=data, follow_redirects=True)

        response = self.client.get("/admin")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="admin-nav"', response_text)
        self.assertNotIn("Login", response_text)
        self.assertIn(self.username, response_text)

    def test_successful_logout_for_autheticated_user(self):
        data = {"email": self.email, "password": self.password}

        self.client.post("/admin", data=data, follow_redirects=True)
        response = self.client.get("/logout", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="admin-nav"', response_text)
        self.assertNotIn("Logout", response_text)
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)

    def test_successful_logout_for_unauthenticated_user(self):
        response = self.client.get("/logout", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="admin-nav"', response_text)
        self.assertNotIn("Logout", response_text)
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)

    def test_create_page_unauthenticated_user(self):
        response = self.client.get("/create")

        self.assertEqual(response.status_code, 401)

    def test_create_page_authenticated_user(self):
        data = {"email": self.email, "password": self.password}
        self.client.post("/admin", data=data, follow_redirects=True)

        response = self.client.get("/create")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("New Post", response_text)
        self.assertIn("Post Editor", response_text)
        self.assertIn("Post Preview", response_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
