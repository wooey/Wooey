from __future__ import absolute_import

from django.urls import include, re_path

from . import api
from . import views
from . import settings as wooey_settings

app_name = "wooey"

wooey_patterns = [
    re_path(r"^jobs/command$", views.celery_task_command, name="celery_task_command"),
    re_path(
        r"^jobs/queue/global/json$", views.global_queue_json, name="global_queue_json"
    ),
    re_path(r"^jobs/queue/user/json$", views.user_queue_json, name="user_queue_json"),
    re_path(
        r"^jobs/results/user/json$", views.user_results_json, name="user_results_json"
    ),
    re_path(r"^jobs/queue/all/json", views.all_queues_json, name="all_queues_json"),
    re_path(
        r"^jobs/queue/global", views.GlobalQueueView.as_view(), name="global_queue"
    ),
    re_path(r"^jobs/queue/user", views.UserQueueView.as_view(), name="user_queue"),
    re_path(
        r"^jobs/results/user", views.UserResultsView.as_view(), name="user_results"
    ),
    re_path(
        r"^jobs/(?P<job_id>[0-9\-]+)/$", views.JobView.as_view(), name="celery_results"
    ),
    re_path(
        r"^jobs/(?P<job_id>[0-9\-]+)/json$",
        views.JobJSON.as_view(),
        name="celery_results_json",
    ),
    re_path(
        r"^jobs/(?P<job_id>[0-9\-]+)/jsonhtml$",
        views.JobJSONHTML.as_view(),
        name="celery_results_json_html",
    ),
    # Global public access via uuid
    re_path(
        r"^jobs/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12})/$",
        views.JobView.as_view(),
        name="celery_results_uuid",
    ),
    re_path(
        r"^jobs/(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12})/json$",
        views.JobJSON.as_view(),
        name="celery_results_json_uuid",
    ),
    re_path(
        r"^api/scripts/v1/(?P<slug>[a-zA-Z0-9\-\_]+)/submit/$",
        api.submit_script,
        name="api_submit_script",
    ),
    re_path(
        r"^api/scripts/v1/add-or-update/$",
        api.add_or_update_script,
        name="api_add_or_update_script",
    ),
    re_path(
        r"^api/jobs/v1/(?P<job_id>[a-zA-Z0-9\-\_]+)/status/$",
        api.job_status,
        name="api_job_status",
    ),
    re_path(
        r"^api/jobs/v1/(?P<job_id>[a-zA-Z0-9\-\_]+)/details/$",
        api.job_details,
        name="api_job_details",
    ),
    re_path(
        r"^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/$",
        views.WooeyScriptView.as_view(),
        name="wooey_script",
    ),
    re_path(
        r"^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/version/(?P<script_version>[^/]+)$",
        views.WooeyScriptView.as_view(),
        name="wooey_script",
    ),
    re_path(
        r"^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/version/(?P<script_version>[^/]+)/iteration/(?P<script_iteration>\d+)$",
        views.WooeyScriptView.as_view(),
        name="wooey_script",
    ),
    re_path(
        r"^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/version/(?P<script_version>[^/]+)/jobs/(?P<job_id>[a-zA-Z0-9\-]+)$",
        views.WooeyScriptView.as_view(),
        name="wooey_script",
    ),
    re_path(
        r"^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/version/(?P<script_version>[^/]+)/iteration/(?P<script_iteration>\d+)/jobs/(?P<job_id>[a-zA-Z0-9\-]+)$",
        views.WooeyScriptView.as_view(),
        name="wooey_script",
    ),
    re_path(
        r"^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/jobs/(?P<job_id>[a-zA-Z0-9\-]+)$",
        views.WooeyScriptView.as_view(),
        name="wooey_script_clone",
    ),
    re_path(
        r"^scripts/(?P<slug>[a-zA-Z0-9\-\_]+)/$",
        views.WooeyScriptJSON.as_view(),
        name="wooey_script_json",
    ),
    re_path(
        r"^scripts/search/json$",
        views.WooeyScriptSearchJSON.as_view(),
        name="wooey_search_script_json",
    ),
    re_path(
        r"^scripts/search/jsonhtml$",
        views.WooeyScriptSearchJSONHTML.as_view(),
        name="wooey_search_script_jsonhtml",
    ),
    re_path(r"^profile/$", views.WooeyProfileView.as_view(), name="profile_home"),
    re_path(
        r"^profile/(?P<username>[a-zA-Z0-9\-]+)$",
        views.WooeyProfileView.as_view(),
        name="profile",
    ),
    re_path(
        r"^settings/api-keys/new/$",
        views.create_api_key,
        name="create_api_key",
    ),
    re_path(
        r"^settings/api-keys/(?P<id>\d+)/delete/$",
        views.delete_api_key,
        name="delete_api_key",
    ),
    re_path(
        r"^settings/api-keys/(?P<id>\d+)/toggle/$",
        views.toggle_api_key,
        name="toggle_api_key",
    ),
    re_path(r"^$", views.WooeyHomeView.as_view(), name="wooey_home"),
    re_path(r"^$", views.WooeyHomeView.as_view(), name="wooey_job_launcher"),
    re_path(
        "^{}".format(wooey_settings.WOOEY_LOGIN_URL.lstrip("/")),
        views.wooey_login,
        name="wooey_login",
    ),
    re_path(r"^favorite/toggle$", views.toggle_favorite, name="toggle_favorite"),
    re_path(r"^scrapbook$", views.WooeyScrapbookView.as_view(), name="scrapbook"),
    re_path(r"^i18n/", include("django.conf.urls.i18n"), name="set_language"),
]

if wooey_settings.WOOEY_REGISTER_URL:
    wooey_patterns += [
        re_path(
            r"^{}".format(wooey_settings.WOOEY_REGISTER_URL.lstrip("/")),
            views.WooeyRegister.as_view(),
            name="wooey_register",
        ),
    ]

urlpatterns = [
    re_path(r"^", include(wooey_patterns)),
]
