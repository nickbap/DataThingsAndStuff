import unittest

from flask import current_app

from config import config
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
        self.assertTrue(current_app.config["TESTING"])
        self.assertEqual(current_app.config["ENV"], "testing")

    def test_home_route(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)


class TestDevelopmentAppConfig(unittest.TestCase):
    def setUp(self):
        self.app = create_app("development")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_app_development_config(self):
        self.assertTrue(current_app.config["DEBUG"])
        self.assertEqual(current_app.config["ENV"], "development")


class TestProductionAppConfig(unittest.TestCase):
    def setUp(self):
        self.app = create_app("production")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_app_production_config(self):
        self.assertFalse(current_app.config["DEBUG"])
        self.assertEqual(current_app.config["ENV"], "production")


if __name__ == "__main__":
    unittest.main(verbosity=2)
