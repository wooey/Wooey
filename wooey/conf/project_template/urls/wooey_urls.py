from .django_urls import *
from django.conf.urls import include, url

urlpatterns += [
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('wooey.urls')),
]
