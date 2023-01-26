from django.urls import include, path

from .django_urls import *

urlpatterns += [
    # path('admin/', include(admin.site.urls)),
    path('', include('wooey.urls')),
    path('', include('django.contrib.auth.urls')),
]
