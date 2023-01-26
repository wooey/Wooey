from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import test_settings

# the DEBUG setting in test_settings is not respected
settings.DEBUG = True


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('wooey.urls')),
    path('', include('django.contrib.auth.urls')),
]

urlpatterns += static(test_settings.MEDIA_URL, document_root=test_settings.MEDIA_ROOT)
urlpatterns += static(test_settings.STATIC_URL, document_root=test_settings.STATIC_ROOT)
