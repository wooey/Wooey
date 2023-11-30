__author__ = "chris"

import os
import tempfile

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from celery import app

celery_app = app.app_or_default()


def get(key, default):
    return getattr(settings, key, default)


IS_WINDOWS = os.name == "nt"

# AUTH based settings
WOOEY_ALLOW_ANONYMOUS = get("WOOEY_ALLOW_ANONYMOUS", True)
WOOEY_AUTH = get("WOOEY_AUTH", True)
WOOEY_LOGIN_URL = get("WOOEY_LOGIN_URL", settings.LOGIN_URL)
WOOEY_REGISTER_URL = get("WOOEY_REGISTER_URL", "/accounts/register/")
WOOEY_ENABLE_API_KEYS = get("WOOEY_ENABLE_API_KEYS", False)

# Celery and job queue settings
WOOEY_CELERY = get("WOOEY_CELERY", True)
WOOEY_CELERY_TASKS = get("WOOEY_CELERY_TASKS", "wooey.tasks")
WOOEY_CELERY_STOPPABLE_JOBS = "amqp" in str(
    celery_app.conf.get("CELERY_BROKER_URL", celery_app.conf.get("broker_url") or "")
)

# Site setup settings
WOOEY_DEFAULT_SCRIPT_GROUP = get("WOOEY_DEFAULT_SCRIPT_GROUP", _("Scripts"))
WOOEY_EPHEMERAL_FILES = get("WOOEY_EPHEMERAL_FILES", False)
WOOEY_FILE_DIR = get("WOOEY_FILE_DIR", "wooey_files")
WOOEY_JOB_EXPIRATION = get("WOOEY_JOB_EXPIRATION", {"anonymous": None, "users": None})
WOOEY_REALTIME_CACHE = get("WOOEY_REALTIME_CACHE", None)
WOOEY_SCRIPT_DIR = get("WOOEY_SCRIPT_DIR", "wooey_scripts")

# User interface settings
WOOEY_SHOW_LOCKED_SCRIPTS = get("WOOEY_SHOW_LOCKED_SCRIPTS", True)
WOOEY_SITE_NAME = get("WOOEY_SITE_NAME", _("Wooey!"))
WOOEY_SITE_TAG = get("WOOEY_SITE_TAG", _("A web UI for Python scripts"))

# Virtual Environment Settings
WOOEY_VIRTUAL_ENVIRONMENT_DIRECTORY = get(
    "WOOEY_VIRTUAL_ENVIRONMENT_DIRECTORY", tempfile.gettempdir()
)
