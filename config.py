import os
from logging import DEBUG

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "ISolemnlySwearImUpToNoGood"


class TestingConfig(Config):
    TESTING = True


config = {
    "config": Config,
    "testing": TestingConfig,
}
