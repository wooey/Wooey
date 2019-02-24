from __future__ import absolute_import

from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static

from . import views
from . import settings as wooey_settings

app_name = 'wooey'

wooey_patterns = [
    url(r'^jobs/command$', views.celery_task_command, name='celery_task_command'),

    url(r'^jobs/queue/global/json$', views.global_queue_json, name='global_queue_json'),
    url(r'^jobs/queue/user/json$', views.user_queue_json, name='user_queue_json'),
    url(r'^jobs/results/user/json$', views.user_results_json, name='user_results_json'),

    url(r'^jobs/queue/all/json', views.all_queues_json, name='all_queues_json'),

    url(r'^jobs/queue/global', views.GlobalQueueView.as_view(), name='global_queue'),
    url(r'^jobs/queue/user', views.UserQueueView.as_view(), name='user_queue'),
    url(r'^jobs/results/user', views.UserResultsView.as_view(), name='user_results'),


    url(r'^jobs/(?P<job_id>[0-9\-]+)/$', views.JobView.as_view(), name='celery_results'),
    url(r'^jobs/(?P<job_id>[0-9\-]+)/json$', views.JobJSON.as_view(), name='celery_results_json'),
    url(r'^jobs/(?P<job_id>[0-9\-]+)/jsonhtml$', views.JobJSONHTML.as_view(), name='celery_results_json_html'),

    # Global public access via uuid
    url(r'^jobs/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12})/$', views.JobView.as_view(), name='celery_results_uuid'),
    url(r'^jobs/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12})/json$', views.JobJSON.as_view(), name='celery_results_json_uuid'),


    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/$', views.WooeyScriptView.as_view(), name='wooey_script'),
    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/version/(?P<script_version>[A-Za-z\.0-9]+)$', views.WooeyScriptView.as_view(), name='wooey_script'),
    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/version/(?P<script_version>[A-Za-z\.0-9]+)/iteration/(?P<script_iteration>\d+)$', views.WooeyScriptView.as_view(), name='wooey_script'),
    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/version/(?P<script_version>[A-Za-z\.0-9]+)/jobs/(?P<job_id>[a-zA-Z0-9\-]+)$', views.WooeyScriptView.as_view(), name='wooey_script'),
    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/version/(?P<script_version>[A-Za-z\.0-9]+)/iteration/(?P<script_iteration>\d+)/jobs/(?P<job_id>[a-zA-Z0-9\-]+)$', views.WooeyScriptView.as_view(), name='wooey_script'),
    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/jobs/(?P<job_id>[a-zA-Z0-9\-]+)$', views.WooeyScriptView.as_view(), name='wooey_script_clone'),
    url(r'^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/$', views.WooeyScriptJSON.as_view(), name='wooey_script_json'),

    url(r'^scripts/search/json$', views.WooeyScriptSearchJSON.as_view(), name='wooey_search_script_json'),
    url(r'^scripts/search/jsonhtml$', views.WooeyScriptSearchJSONHTML.as_view(), name='wooey_search_script_jsonhtml'),


    url(r'^profile/$', views.WooeyProfileView.as_view(), name='profile_home'),
    url(r'^profile/(?P<username>[a-zA-Z0-9\-]+)$', views.WooeyProfileView.as_view(), name='profile'),

    url(r'^$', views.WooeyHomeView.as_view(), name='wooey_home'),
    url(r'^$', views.WooeyHomeView.as_view(), name='wooey_job_launcher'),
    url('^{}'.format(wooey_settings.WOOEY_LOGIN_URL.lstrip('/')), views.wooey_login, name='wooey_login'),

    url(r'^favorite/toggle$', views.toggle_favorite, name='toggle_favorite'),

    url(r'^scrapbook$', views.WooeyScrapbookView.as_view(), name='scrapbook'),


    url(r'^i18n/', include('django.conf.urls.i18n'), name='set_language'),

]

if wooey_settings.WOOEY_REGISTER_URL:
    wooey_patterns += [
        url(r'^{}'.format(wooey_settings.WOOEY_REGISTER_URL.lstrip('/')), views.WooeyRegister.as_view(), name='wooey_register'),
    ]

urlpatterns = [
    url(r'^', include(wooey_patterns)),
]
