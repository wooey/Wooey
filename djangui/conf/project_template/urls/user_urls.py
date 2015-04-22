from .djangui_urls import urlpatterns

from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns += [
    url(r'^', include('djguihome.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)