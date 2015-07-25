from __future__ import absolute_import

from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static

from . import views
from . import settings as wooey_settings

wooey_patterns = [
    url(r'^jobs/command$', views.celery_task_command, name='celery_task_command'),

    url(r'^jobs/queue/global/json$', views.global_queue_json, name='global_queue_json'),
    url(r'^profile/queue/json$', views.user_queue_json, name='user_queue_json'),
    url(r'^profile/results/json$', views.user_results_json, name='user_results_json'),

    url(r'^jobs/queue/all/json', views.all_queues_json, name='all_queues_json'),

    url(r'^jobs/(?P<job_id>[a-zA-Z0-9\-]+)/$', views.CeleryTaskView.as_view(), name='celery_results_info'),

    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/$', views.WooeyScriptView.as_view(), name='wooey_script'),
    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/jobs/(?P<job_id>[a-zA-Z0-9\-]+)$', views.WooeyScriptJSON.as_view(), name='wooey_script_json_clone'),
    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/$', views.WooeyScriptJSON.as_view(), name='wooey_script_json'),

    url(r'^profile/$', views.WooeyProfileView.as_view(), name='profile_home'),
    url(r'^$', views.WooeyHomeView.as_view(), name='wooey_home'),
    url(r'^$', views.WooeyHomeView.as_view(), name='wooey_task_launcher'),
    url('^{}'.format(wooey_settings.WOOEY_LOGIN_URL.lstrip('/')), views.wooey_login, name='wooey_login'),
    url('^{}'.format(wooey_settings.WOOEY_REGISTER_URL.lstrip('/')), views.WooeyRegister.as_view(), name='wooey_register'),

    url(r'^favorite/toggle$', views.toggle_favorite, name='toggle_favorite'),

    url(r'^scrapbook$', views.WooeyScrapbookView.as_view(), name='scrapbook'),

]

urlpatterns = [
    url('^', include(wooey_patterns, namespace='wooey')),
    url('^', include('django.contrib.auth.urls')),
]
