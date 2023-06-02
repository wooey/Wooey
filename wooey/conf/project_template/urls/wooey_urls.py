from .django_urls import *  # noqa: F403
from django.urls import include, path

urlpatterns += [  # noqa: F405
    # path('admin/', include(admin.site.urls)),
    path("", include("wooey.urls")),
    path("", include("django.contrib.auth.urls")),
]
