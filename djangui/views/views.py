import json

from django.views.generic import TemplateView, DetailView
from django.http import JsonResponse
from django.conf import settings
from django.forms import FileField
from django.core.files.storage import default_storage
from django.forms.models import model_to_dict

from djangui.backend import utils
from djangui.views.mixins import DjanguiScriptMixin
from ..models import DjanguiJob, Script


class DjanguiScriptJSON(DetailView):
    model = Script
    slug_field = 'slug'
    slug_url_kwarg = 'script_name'

    def render_to_response(self, context, **response_kwargs):
        # returns the models required and optional fields as html
        # import pdb; pdb.set_trace();
        task_id = self.kwargs.get('task_id')
        initial = None
        if task_id:
            job = DjanguiJob.objects.get(celery_id=task_id)
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
        if request.user.is_authenticated() or not settings.DJANGUI_ALLOW_ANONYMOUS:
            post['user'] = request.user
        form = utils.get_master_form(pk=post['djangui_type'])
        # TODO: Check with people who know more if there's a smarter way to do this
        form.add_djangui_fields()
        form.data = post
        form.files = request.FILES
        form.is_bound = True
        form.full_clean()

        if not form.is_valid():
            # for cloned jobs, we have the files named in 'currently'. This will cause validation issues.
            to_delete = []
            for i in post:
                if isinstance(form.fields.get(i), FileField):
                    # if we have a value set, reassert this
                    to_delete.append(i)
                    if i not in request.FILES and (i not in form.cleaned_data or form.cleaned_data[i] is None):
                        # this is a previously set field, so a cloned job
                        form.cleaned_data[i] = default_storage.open(post.get(i))
            for i in to_delete:
                if i in form.errors:
                    del form.errors[i]

        if not form.errors:
            data = form.cleaned_data
            job, com = form.save()
            job.submit_to_celery(command=com)
            return JsonResponse({'valid': True})

        return JsonResponse({'valid': False, 'errors': form.errors})


class DjanguiScriptHome(DjanguiScriptMixin, TemplateView):
    template_name = 'scripts_home.html'

    def get_context_data(self, **kwargs):
        ctx = super(DjanguiScriptHome, self).get_context_data(**kwargs)
        ctx['scripts'] = []
        # import pdb; pdb.set_trace();
        for model in dir(self.djangui_models):
            if model == 'DjanguiModel':
                continue
            klass = getattr(self.djangui_models, model)
            try:
                if klass._meta.app_label == self.app_name:
                    ctx['scripts'].append({
                        'name': klass._meta.object_name,
                        'objects': klass.objects.all(),
                        'url': utils.get_model_script_url(klass, json=False)
                    })
            except AttributeError:
                continue
        return ctx