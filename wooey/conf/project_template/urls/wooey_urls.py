from .django_urls import *
from django.urls import include, path

urlpatterns += [
    # path('admin/', include(admin.site.urls)),
    path('', include('wooey.urls')),
    path('', include('django.contrib.auth.urls')),
]
