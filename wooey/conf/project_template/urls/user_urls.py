from django.conf import settings
from django.conf.urls.static import static

from .wooey_urls import *  # noqa: F403

if settings.DEBUG:
    urlpatterns += static(  # noqa: F405
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(  # noqa: F405
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
