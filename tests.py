import unittest
from datetime import datetime

from flask import current_app
from werkzeug.security import generate_password_hash

from dtns import create_app
from dtns import db
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
        self.assertIn("Login", response_text)
        self.assertNotIn(self.username, response_text)
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)

    def test_successful_admin_login(self):
        data = {"email": self.email, "password": self.password}

        response = self.client.post("/admin", data=data, follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
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
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)

    def test_admin_page_for_autheticated_user(self):
        data = {"email": self.email, "password": self.password}
        self.client.post("/admin", data=data, follow_redirects=True)

        response = self.client.get("/admin")
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Login", response_text)
        self.assertIn(self.username, response_text)

    def test_successful_logout_for_autheticated_user(self):
        data = {"email": self.email, "password": self.password}

        self.client.post("/admin", data=data, follow_redirects=True)
        response = self.client.get("/logout", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Logout", response_text)
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)

    def test_successful_logout_for_unauthenticated_user(self):
        response = self.client.get("/logout", follow_redirects=True)
        response_text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Logout", response_text)
        self.assertNotIn("New Post", response_text)
        self.assertNotIn('id="post-list"', response_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
