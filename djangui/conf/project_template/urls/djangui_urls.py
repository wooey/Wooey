from .django_urls import *

urlpatterns += [
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('djguicore.urls')),
    url(r'^', include('{{ app_name }}.urls')),
]