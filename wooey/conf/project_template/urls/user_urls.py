from os import environ

from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static

from .wooey_urls import *

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
