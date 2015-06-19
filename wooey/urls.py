from __future__ import absolute_import

from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static

# from wooey.admin import
from .views import (celery_status, CeleryTaskView, celery_task_command, WooeyScriptJSON,
                           WooeyHomeView, WooeyRegister, wooey_login, WooeyProfileView)

from . import settings as wooey_settings

wooey_patterns = [
    url(r'^celery/command$', celery_task_command, name='celery_task_command'),
    url(r'^celery/status$', celery_status, name='celery_results'),
    url(r'^celery/(?P<job_id>[a-zA-Z0-9\-]+)/$', CeleryTaskView.as_view(), name='celery_results_info'),
    # url(r'^admin/', include(wooey_admin.urls)),
    url(r'^djscript/(?P<script_group>[a-zA-Z0-9\-\_]+)/(?P<script_name>[a-zA-Z0-9\-\_]+)/(?P<job_id>[a-zA-Z0-9\-]+)$',
        WooeyScriptJSON.as_view(), name='wooey_script_clone'),
    url(r'^djscript/(?P<script_group>[a-zA-Z0-9\-\_]+)/(?P<script_name>[a-zA-Z0-9\-\_]+)/$', WooeyScriptJSON.as_view(), name='wooey_script'),
    url(r'^profile/$', WooeyProfileView.as_view(), name='profile_home'),
    url(r'^$', WooeyHomeView.as_view(), name='wooey_home'),
    url(r'^$', WooeyHomeView.as_view(), name='wooey_task_launcher'),
    url('^{}'.format(wooey_settings.WOOEY_LOGIN_URL.lstrip('/')), wooey_login, name='wooey_login'),
    url('^{}'.format(wooey_settings.WOOEY_REGISTER_URL.lstrip('/')), WooeyRegister.as_view(), name='wooey_register'),
]

urlpatterns = [
    url('^', include(wooey_patterns, namespace='wooey')),
    url('^', include('django.contrib.auth.urls')),
]
