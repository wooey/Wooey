from . import test_settings
from django.conf import settings
from django.urls import include, path, url
from django.conf.urls.static import static
from django.contrib import admin

# the DEBUG setting in test_settings is not respected
settings.DEBUG = True


urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^', include('wooey.urls')),
    url(r'^', include('django.contrib.auth.urls')),
]

urlpatterns += static(test_settings.MEDIA_URL, document_root=test_settings.MEDIA_ROOT)
urlpatterns += static(test_settings.STATIC_URL, document_root=test_settings.STATIC_ROOT)
