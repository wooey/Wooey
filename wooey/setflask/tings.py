# -*- coding: utf-8 -*-
import os

os_env = os.environ


class Config(object):
    SECRET_KEY = os_env.get('WOOEY_SECRET', 'not-so-secret-key')  # TODO: Change me
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    BCRYPT_LOG_ROUNDS = 13
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.

    SITE_NAME = "Wooey!"
    SITE_TAGLINE = "A web UI for Python scripts."

    QUEUE_MAXIMUM_RUNNING_JOBS = 4  # Maximum number of running jobs (processes)
    QUEUE_MAXIMUM_FINISHED_JOBS = 50  # Maximum number of finished (error/complete) jobs in the Queue

    EXCLUDED_EXTENSIONS_FOR_DOWNLOAD = []
    EXCLUDED_FILES_FOR_DOWNLOAD = []

    EXCLUDED_FILES_FOR_UPLOAD = []
    EXCLUDED_EXTENSIONS_FOR_UPLOAD = []

    GITHUB_URL = "https://github.com/mfitzp/Wooey"

class ProdConfig(Config):
    """Production configuration."""
    ENV = 'prod'
    DEBUG = False
    # Database URL for Heroku deployment is in DATABASE_URL env variable
    SQLALCHEMY_DATABASE_URI = os_env.get('DATABASE_URL', None)
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar


class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    DB_NAME = 'dev.db'
    # Put the db file in project root
    DB_PATH = os.path.join(Config.PROJECT_ROOT, DB_NAME)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}'.format(DB_PATH)
    DEBUG_TB_ENABLED = True
    ASSETS_DEBUG = True  # Don't bundle/minify static assets
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    BCRYPT_LOG_ROUNDS = 1  # For faster tests
    WTF_CSRF_ENABLED = False  # Allows form testing
