try:
    from django.apps import AppConfig
except ImportError:
    AppConfig = object
from django.conf import settings
from . import settings as wooey_settings


class WooeyConfig(AppConfig):
    name = "wooey"
    verbose_name = "Wooey"

    def ready(self):
        from . import signals  # noqa: F401

        if wooey_settings.WOOEY_ENABLE_API_KEYS:
            new_middleware = []
            for value in settings.MIDDLEWARE:
                new_middleware.append(value)
                if value == "django.contrib.auth.middleware.AuthenticationMiddleware":
                    new_middleware.append("wooey.middleware.api_key_login")
            settings.MIDDLEWARE = new_middleware
