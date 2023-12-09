from __future__ import absolute_import, unicode_literals
from collections import defaultdict

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView, View

from ..backend import utils
from ..models import (
    APIKey,
    WooeyJob,
    Script,
    UserFile,
    Favorite,
    ScriptVersion,
    WooeyProfile,
)
from .. import settings as wooey_settings


class WooeyScriptBase(DetailView):
    model = Script
    slug_field = "slug"
    slug_url_kwarg = "slug"

    @staticmethod
    def render_fn(s):
        return s

    def get_context_data(self, **kwargs):
        context = super(WooeyScriptBase, self).get_context_data(**kwargs)
        version = self.kwargs.get("script_version")
        iteration = self.kwargs.get("script_iteration")

        # returns the models required and optional fields as html
        job_id = self.kwargs.get("job_id")
        initial = defaultdict(list)

        if job_id:
            job = WooeyJob.objects.get(pk=job_id)
            if job.can_user_view(self.request.user):
                context["job_info"] = {"job_id": job_id}

                parser_used = None
                for i in job.get_parameters():
                    value = i.value
                    if value is not None:
                        script_parameter = i.parameter
                        if script_parameter.parser.name:
                            parser_used = script_parameter.parser.pk
                        initial[script_parameter.form_slug].append(value)

                if parser_used is not None:
                    initial["wooey_parser"] = parser_used

        script_version = ScriptVersion.objects.filter(
            script=self.object,
        )
        if not (version or iteration):
            script_version = script_version.get(default_version=True)
        else:
            if version:
                script_version = script_version.filter(script_version=version)
            if iteration:
                script_version = script_version.filter(script_iteration=iteration)

            script_version = script_version.order_by(
                "script_version", "script_iteration"
            ).last()

        # Set parameter initial values by parsing the URL parameters
        # and matching them to the script parameters.
        for param in script_version.get_parameters():
            if param.script_param in self.request.GET:
                value = (
                    self.request.GET.getlist(param.script_param)
                    if param.multiple_choice
                    else self.request.GET.get(param.script_param)
                )
                initial[param.form_slug] = value

        context["form"] = utils.get_form_groups(
            script_version=script_version,
            initial_dict=initial,
            render_fn=self.render_fn,
        )

        # Additional script info to display.
        context["script_version"] = script_version.script_version
        context["script_iteration"] = script_version.script_iteration
        context["script_created_by"] = script_version.created_by
        context["script_created_date"] = script_version.created_date
        context["script_modified_by"] = script_version.modified_by
        context["script_modified_date"] = script_version.modified_date
        return context

    def post(self, request, *args, **kwargs):
        post = request.POST.copy()
        user = request.user if request.user.is_authenticated else None
        if not wooey_settings.WOOEY_ALLOW_ANONYMOUS and user is None:
            return {
                "valid": False,
                "errors": {
                    "__all__": [
                        force_str(_("You are not permitted to access this script."))
                    ]
                },
            }

        form = utils.get_master_form(
            pk=int(post["wooey_type"]), parser=int(post.get("wooey_parser", 0))
        )
        utils.validate_form(form=form, data=post, files=request.FILES)

        if not form.errors:
            version_pk = form.cleaned_data.get("wooey_type")
            parser_pk = form.cleaned_data.get("wooey_parser")
            script_version = ScriptVersion.objects.get(pk=version_pk)
            valid = utils.valid_user(script_version.script, request.user).get("valid")
            if valid:
                group_valid = utils.valid_user(
                    script_version.script.script_group, request.user
                )["valid"]
                if valid and group_valid:
                    job = utils.create_wooey_job(
                        script_parser_pk=parser_pk,
                        script_version_pk=version_pk,
                        user=user,
                        data=form.cleaned_data,
                    )
                    job.submit_to_celery()
                    return {"valid": True, "job_id": job.id}

            return {
                "valid": False,
                "errors": {
                    "__all__": [
                        force_str(_("You are not permitted to access this script."))
                    ]
                },
            }

        return {"valid": False, "errors": form.errors}


class WooeyScriptJSON(WooeyScriptBase):

    # FIXME: the form data is returned as form objects so can be passed to templates
    # this render_fn allows us to pass the return through a stringify method for JSON
    @staticmethod
    def render_fn(form):
        return form.as_table()

    def render_to_response(self, context, *args, **kwargs):
        return JsonResponse(context)

    def post(self, *args, **kwargs):
        data = super(WooeyScriptJSON, self).post(*args, **kwargs)
        return JsonResponse(data)


class WooeyScriptView(WooeyScriptBase):

    template_name = "wooey/scripts/script_view.html"

    def post(self, *args, **kwargs):
        data = super(WooeyScriptView, self).post(*args, **kwargs)
        if data["valid"]:
            data["redirect"] = reverse(
                "wooey:celery_results", kwargs={"job_id": data["job_id"]}
            )
        return JsonResponse(data)


class WooeyHomeView(TemplateView):
    template_name = "wooey/home.html"

    def get_context_data(self, **kwargs):
        # job_id = self.request.GET.get('job_id')
        ctx = super(WooeyHomeView, self).get_context_data(**kwargs)
        ctx["scripts"] = utils.get_current_scripts()

        # Check for logged in user
        if self.request.user.is_authenticated:
            # Get the id of every favorite (scrapbook) file
            ctype = ContentType.objects.get_for_model(Script)
            favorite_scripts = Favorite.objects.filter(
                content_type=ctype, user__id=self.request.user.id
            ).values_list("object_id", flat=True)
            ctx["favorite_script_ids"] = favorite_scripts
            # put favorite scripts at the top of the sort order
            ctx["scripts"] = sorted(
                ctx["scripts"],
                # we do the `not` so we can sort in ascending order for both the
                # favorite status and get alphabetical sorting
                key=lambda x: (x.id not in favorite_scripts, x.script_name),
            )
        else:
            ctx["favorite_script_ids"] = []

        return ctx


class WooeyProfileView(TemplateView):
    template_name = "wooey/profile/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super(WooeyProfileView, self).get_context_data(**kwargs)

        user = None
        if "username" in self.kwargs:
            User = get_user_model()
            user = User.objects.get(username=self.kwargs.get("username"))
        else:
            if self.request.user and self.request.user.is_authenticated:
                user = self.request.user

        ctx["user_obj"] = user
        is_logged_in_user = False

        if self.request.user.is_authenticated:
            user_profile, _ = WooeyProfile.objects.get_or_create(user=user)
            ctx["user_profile"] = user_profile
            is_logged_in_user = user_profile.user == self.request.user

            if is_logged_in_user:
                ctx["api_keys"] = [
                    {
                        "id": i.id,
                        "name": i.name,
                        "active": i.active,
                        "created_date": i.created_date,
                        "last_used": i.last_used,
                    }
                    for i in APIKey.objects.filter(profile=user_profile)
                ]

        ctx["is_logged_in_user"] = is_logged_in_user

        return ctx


class WooeyScrapbookView(TemplateView):
    template_name = "wooey/scrapbook.html"

    def get_context_data(self, **kwargs):
        ctx = super(WooeyScrapbookView, self).get_context_data(**kwargs)

        # Get the id of every favorite (scrapbook) file
        ctype = ContentType.objects.get_for_model(UserFile)
        favorite_file_ids = Favorite.objects.filter(
            content_type=ctype, user=self.request.user
        ).values_list("object_id", flat=True)

        out_files = utils.get_file_previews_by_ids(favorite_file_ids)

        all = out_files.pop("all", [])
        archives = out_files.pop("archives", [])

        ctx["file_groups"] = out_files
        ctx["favorite_file_ids"] = favorite_file_ids

        return ctx


class WooeySearchBase(View):

    model = None
    search_fields = []

    def get(self, request, *args, **kwargs):

        self.search_results = None
        if "q" in request.GET:
            query_string = request.GET["q"].strip()

            query = utils.get_query(query_string, self.search_fields)
            self.search_results = self.model.objects.filter(query)

            return self.search(request, *args, **kwargs)


class WooeyScriptSearchBase(WooeySearchBase):

    model = Script
    search_fields = ["script_name", "script_description"]


class WooeyScriptSearchJSON(WooeyScriptSearchBase):
    """
    Returns the result of the script search as JSON containing data only
    """

    def search(self, request):
        results = []
        for script in self.search_results:
            results.append(
                {
                    "id": script.id,
                    "name": script.script_name,
                    "description": script.script_description,
                    "url": reverse("wooey:wooey_script", kwargs={"slug": script.slug}),
                }
            )
        return JsonResponse({"results": results})


class WooeyScriptSearchJSONHTML(WooeyScriptSearchBase):
    """
    Returns the result of the script search as JSON containing rendered template
    elements for display in the original page. This is a temporary function
    until the handling is moved to client side rendering.
    """

    def search(self, request):
        results = []
        for script in self.search_results:
            results.append(
                render_to_string(
                    "wooey/scripts/script_panel.html",
                    {"script": script, "request": request},
                )
            )
        return JsonResponse({"results": results})
