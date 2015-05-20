from __future__ import absolute_import
from django.views.generic import DetailView, TemplateView, CreateView
from django.http import JsonResponse
from django.conf import settings
from django.forms import FileField
from django.core.files.storage import default_storage
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_unicode

from djangui.backend import utils
from ..models import DjanguiJob, Script
from .. import settings as djangui_settings
from ..templatetags.djangui_tags import valid_user


class DjanguiScriptJSON(DetailView):
    model = Script
    slug_field = 'slug'
    slug_url_kwarg = 'script_name'

    def render_to_response(self, context, **response_kwargs):
        # returns the models required and optional fields as html
        job_id = self.kwargs.get('job_id')
        initial = None
        if job_id:
            job = DjanguiJob.objects.get(pk=job_id)
            if job.user is None or (self.request.user.is_authenticated() and job.user == self.request.user):
                initial = {}
                for i in job.get_parameters():
                    value = i.value
                    if value is not None:
                        initial[i.parameter.slug] = value
        d = utils.get_form_groups(model=self.object, initial=initial)
        return JsonResponse(d)

    def post(self, request, *args, **kwargs):
        post = request.POST.copy()
        if request.user.is_authenticated() or not djangui_settings.DJANGUI_ALLOW_ANONYMOUS:
            post['user'] = request.user
        form = utils.get_master_form(pk=post['djangui_type'])
        # TODO: Check with people who know more if there's a smarter way to do this
        utils.validate_form(form=form, data=post, files=request.FILES)
        # for cloned jobs, we don't have the files in input fields, they'll be in a list like ['', filename]
        # This will cause issues.
        to_delete = []
        for i in post:
            if isinstance(form.fields.get(i), FileField):
                # if we have a value set, reassert this
                new_value = post.get(i)
                if i not in request.FILES and (i not in form.cleaned_data or (not form.cleaned_data[i] and new_value)):
                    # this is a previously set field, so a cloned job
                    if new_value is not None:
                        form.cleaned_data[i] = utils.get_storage(local=False).open(new_value)
                    to_delete.append(i)
        for i in to_delete:
            if i in form.errors:
                del form.errors[i]

        if not form.errors:
            # data = form.cleaned_data
            script = Script.objects.get(pk=form.cleaned_data.get('djangui_type'))
            valid = valid_user(script, request.user).get('valid')
            if valid is True:
                group_valid = valid_user(script.script_group, request.user).get('valid')
                if valid is True and group_valid is True:
                    job = form.save()
                    job.submit_to_celery()
                    return JsonResponse({'valid': True})
            return JsonResponse({'valid': False, 'errors': {'__all__': [force_unicode(_('You are not permitted to access this script.'))]}})
        return JsonResponse({'valid': False, 'errors': form.errors})


class DjanguiHomeView(TemplateView):
    template_name = 'djangui_home.html'

    def get_context_data(self, **kwargs):
        job_id = self.request.GET.get('job_id')
        ctx = super(DjanguiHomeView, self).get_context_data(**kwargs)
        ctx['djangui_scripts'] = getattr(settings, 'DJANGUI_SCRIPTS', {})
        if job_id:
            job = DjanguiJob.objects.get(pk=job_id)
            if job.user is None or (self.request.user.is_authenticated() and job.user == self.request.user):
                ctx['clone_job'] = {'job_id': job_id, 'url': job.get_resubmit_url(), 'data_url': job.script.get_url()}
        return ctx