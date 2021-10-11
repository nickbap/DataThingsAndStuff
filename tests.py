import unittest
from datetime import datetime

from flask import current_app

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
