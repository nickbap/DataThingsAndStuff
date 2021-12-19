import unittest

from flask import current_app

from dtns import create_app


class TestingAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_app_is_testing(self):
        self.assertTrue(current_app.config["TESTING"])

    def test_app_is_not_debugging(self):
        self.assertFalse(current_app.config["DEBUG"])

    def test_sentry_dsn_is_none(self):
        self.assertIsNone(current_app.config["SENTRY_DSN"])


class AppConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_app_production_env(self):
        self.assertEqual(current_app.config["ENV"], "production")

    def test_app_is_not_testing(self):
        self.assertFalse(current_app.config["TESTING"])

    def test_app_is_not_debugging(self):
        self.assertFalse(current_app.config["DEBUG"])

    def test_sentry_dsn_is_not_none(self):
        self.assertIsNotNone(current_app.config["SENTRY_DSN"])
