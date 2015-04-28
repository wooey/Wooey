from django.conf.urls import include, url

from .admin import djangui_admin
from djangui.views import celery_status, CeleryTaskView, celery_task_command, DjanguiScriptJSON


urlpatterns = [
    url(r'^celery/command$', celery_task_command, name='celery_task_command'),
    url(r'^celery/status$', celery_status, name='celery_results'),
    url(r'^celery/(?P<task_id>[a-zA-Z0-9\-]+)/$', CeleryTaskView.as_view(), name='celery_results_info'),
    url(r'^djangui-admin/', include(djangui_admin.urls)),
    url(r'^djscript/(?P<script_group>[a-zA-Z0-9\-\_]+)/(?P<script_name>[a-zA-Z0-9\-\_]+)/(?P<task_id>[a-zA-Z0-9\-]+)$',
        DjanguiScriptJSON.as_view(), name='djangui_script_clone'),
    url(r'^djscript/(?P<script_group>[a-zA-Z0-9\-\_]+)/(?P<script_name>[a-zA-Z0-9\-\_]+)/$', DjanguiScriptJSON.as_view(), name='djangui_script'),
]