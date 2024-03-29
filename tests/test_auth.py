import unittest

from werkzeug.security import generate_password_hash

from dtns import create_app
from dtns import db
from dtns.models import User


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        self.admin_user_email = "test@test.com"
        self.admin_user_username = "test_user"
        self.admin_user_password = "test_password"
        self.admin_user_password_hash = generate_password_hash(self.admin_user_password)
        self.is_admin = True

        self.admin_user = User(
            email=self.admin_user_email,
            username=self.admin_user_username,
            password=self.admin_user_password_hash,
            is_admin=self.is_admin,
        )

        db.session.add(self.admin_user)
        db.session.commit()

    def tearDown(self):
        db.session.commit()
        db.drop_all()
        self.app_context.pop()

    def test_admin_page_for_unautheticated_user(self):
        response = self.client.get("/admin")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="admin-nav"', response_text)
        self.assertIn("Login", response_text)
        self.assertNotIn(self.admin_user_username, response_text)
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)

    def test_successful_admin_login(self):
        data = {"email": self.admin_user_email, "password": self.admin_user_password}

        response = self.client.post("/admin", data=data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="admin-nav"', response_text)
        self.assertIn("Welcome to Data Things and Stuff!", response_text)
        self.assertIn("success", response_text)
        self.assertIn("Admin", response_text)
        self.assertIn('id="admin-options"', response_text)

    def test_unsuccessful_admin_login(self):
        data = {"email": self.admin_user_email, "password": "aWrongPassWord"}

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
        data = {"email": self.admin_user_email, "password": self.admin_user_password}
        self.client.post("/admin", data=data, follow_redirects=True)

        response = self.client.get("/admin")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="admin-nav"', response_text)
        self.assertNotIn("Login", response_text)
        self.assertIn(self.admin_user_username, response_text)

    def test_admin_page_for_comment_only_user(self):
        email = "ionlycomment@test.com"
        username = "ionlycomment"
        password = "i-only-comment"
        comment_user = User(email=email, username=username, password=password)
        db.session.add(comment_user)
        db.session.commit()
        data = {"email": email, "password": password}

        response = self.client.post("/admin", data=data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Commenters are not allowed to log in!", response_text)
        self.assertIn("danger", response_text)

    def test_admin_page_for_nonexistent_user(self):
        data = {"email": "wontfindme@noone.com", "password": "doesnotmatter"}

        response = self.client.post("/admin", data=data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Something went wrong with your login! Please try again.", response_text
        )
        self.assertIn("danger", response_text)

    def test_successful_logout_for_autheticated_user(self):
        data = {"email": self.admin_user_email, "password": self.admin_user_password}

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
        data = {"email": self.admin_user_email, "password": self.admin_user_password}
        self.client.post("/admin", data=data, follow_redirects=True)

        response = self.client.get("/create")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("New Post", response_text)
        self.assertIn("Post Editor", response_text)
        self.assertIn("Post Preview", response_text)
