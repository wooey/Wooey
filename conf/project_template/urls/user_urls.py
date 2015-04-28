from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static

from .djangui_urls import *

urlpatterns += [
    url(r'^', include(settings.DJANGUI_HOME_URLS)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)