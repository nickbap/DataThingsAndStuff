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
