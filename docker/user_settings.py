import os
from .wooey_settings import *  # noqa: F403

# Whether to allow anonymous job submissions, set False to disallow 'guest' job submissions
WOOEY_ALLOW_ANONYMOUS = True

WOOEY_ENABLE_API_KEYS = True

WOOEY_REALTIME_CACHE = "default"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://redis:6379",
    }
}

## Celery related options
WOOEY_CELERY = True

# the directory for uploads (physical directory)
MEDIA_ROOT = os.path.join(BASE_DIR, "user_uploads")  # noqa: F405
# the url mapping
MEDIA_URL = "/uploads/"

# the directory to store our webpage assets (images, javascript, etc.)
STATIC_ROOT = os.path.join(BASE_DIR, "static")  # noqa: F405
# the url mapping
STATIC_URL = "/static/"
## Here is a setup example for production servers

## A postgres database -- for multiple users a sqlite based database is asking for trouble

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        # for production environments, these should be stored as environment variables
        # I also recommend the django-heroku-postgresify package for a super simple setup
        "NAME": os.environ.get("DATABASE_NAME", "wooey"),
        "USER": os.environ.get("DATABASE_USER", "wooey"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "wooey"),
        "HOST": os.environ.get("DATABASE_URL", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
    }
}

ALLOWED_HOSTS = (
    "localhost",
    "127.0.0.1",
)

AUTHENTICATION_BACKEND = "django.contrib.auth.backends.ModelBackend"
