from django.conf.urls import include, url
from django.contrib import admin

from .views import DjanguiScriptCreate, DjanguiScriptEdit, DjanguiScriptHome


urlpatterns = [
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^script/(?P<script_name>[a-zA-Z0-9\_]+)/(?P<pk>\d+)/$', DjanguiScriptEdit.as_view(), name='{{ app_name }}_script_edit'),
    url(r'^script/(?P<script_name>[a-zA-Z0-9\_]+)/$', DjanguiScriptCreate.as_view(), name='{{ app_name }}_script'),
    url(r'^script/$', DjanguiScriptHome.as_view(), name='{{ app_name }}_home'),
]
