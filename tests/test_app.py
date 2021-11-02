import unittest

from flask import current_app

from dtns import create_app


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
