from .django_urls import *
from django.conf.urls import include, url

urlpatterns += [
    # path('admin/', include(admin.site.urls)),
    url(r'^', include('wooey.urls')),
    url(r'^', include('django.contrib.auth.urls')),
]
