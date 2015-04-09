from django.conf.urls import include, url
from django.contrib import admin

from .views import DjanguiScriptCreate, DjanguiScriptEdit, DjanguiScriptHome

script_patterns = [
    url(r'^(?P<script_name>[a-zA-Z0-9\_]+)/(?P<pk>\d+)/$', DjanguiScriptEdit.as_view(), name='{{ app_name }}_script_edit'),
    url(r'^(?P<script_name>[a-zA-Z0-9\_]+)/$', DjanguiScriptCreate.as_view(), name='{{ app_name }}_script'),
    url(r'^$', DjanguiScriptHome.as_view(), name='{{ app_name }}_home'),
]

urlpatterns = [
    #url(r'^admin/', include(admin.site.urls)),
    url(r'{{ app_name }}/', include(script_patterns)),
]
