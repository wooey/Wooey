try:
    from django.http import JsonResponse
except ImportError:
    # TODO: make these fallbacks work
    from django.http import HttpResponse
    import json
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models.base import ModelBase
from django.forms.models import modelform_factory
from django.views.generic import CreateView, UpdateView, TemplateView, View
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_unicode
from django.conf import settings

from djangui.backend import utils
from djangui.db import fields as djangui_fields

from djguicore.models import DjanguiJob

from .models import djangui_models
# Create your views here.

# TODO: Figure out how to make this entire file a single copy instead of in each app

class DjanguiScriptMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.script_name = kwargs.pop('script_name')
        klass = getattr(djangui_models, self.script_name)
        self.model = klass
        return super(DjanguiScriptMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        klass = getattr(djangui_models, self.script_name)
        return klass.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super(DjanguiScriptMixin, self).get_context_data(**kwargs)
        ctx['script_name'] = self.script_name
        return ctx

    def get_form_class(self):
        return modelform_factory(self.model, fields=self.fields, exclude=('djangui_script_name', 'djangui_celery_id', 'djangui_celery_state'))


class DjanguiScriptEdit(DjanguiScriptMixin, UpdateView):
    template_name = 'generic_script_view.html'
    fields = '__all__'


class DjanguiScriptCreate(DjanguiScriptMixin, CreateView):
    fields = '__all__'
    template_name = 'generic_script_create.html'
    success_url = reverse_lazy(getattr(settings, 'POST_SCRIPT_URL', '{{ app_name }}_home'))

class DjanguiScriptJSON(DjanguiScriptMixin, View):
    def get(self, request, *args, **kwargs):
        # returns the models required and optional fields as html
        task_id = request.GET.get('task_id')
        instance = None
        if task_id:
            job = DjanguiJob.objects.get(djangui_celery_id=task_id)
            if job.djangui_user is None or (request.user.is_authenticated() and job.djangui_user == request.user):
                instance = job.content_object
        d = utils.get_modelform_dict(self.model, instance=instance)
        return JsonResponse(d)

    def post(self, request, *args, **kwargs):
        model_form = modelform_factory(self.model, fields='__all__', exclude=set(settings.DJANGUI_EXCLUDES)-{'djangui_job_name', 'djangui_job_description', 'djangui_user'})
        post = request.POST.copy()
        if request.user.is_authenticated() or not settings.DJANGUI_ALLOW_ANONYMOUS:
            post['djangui_user'] = request.user
        form = model_form(post, request.FILES)
        if form.is_valid():
            # We don't do commit=False here, even though we are saving the model again below in our celery submission.
            # this ensures the file is uploaded if needed.
            model = form.save()
            model.submit_to_celery()
            return JsonResponse({'valid': True})
        # we can not validate due to files not yet being created, which will be created once the script is run.
        # purge these
        deleted_files = {}
        for i in self.model.djangui_output_options:
            if i in form.errors:
                deleted_files[i] = post.get(i, None)
                del form.errors[i]
        # we also cannot validate due to files not being replaced, though they are set such as when cloning a job
        files_to_sync = set([])
        for i in self.model._meta.fields:
            if issubclass(type(i), djangui_fields.DjanguiUploadFileField):
                if post.get(i.name):
                    if i.name in form.errors:
                        del form.errors[i.name]
                    files_to_sync.add(i.name)
        if not form.errors:
            model = form.save(commit=False)
            # update our instance with where we want to save files if the user specified it
            for i,v in deleted_files.iteritems():
                if v:
                    try:
                        model._djangui_temp_output[i] = v[0] if isinstance(v, list) else v
                    except AttributeError:
                        model._djangui_temp_output = {i: v[0] if isinstance(v, list) else v}
            # update out instance with any referenced files
            if files_to_sync:
                parent = DjanguiJob.objects.get(djangui_celery_id=post.get('djangui_clone_task_id')).content_object
                for model_field in files_to_sync:
                    setattr(model, model_field, getattr(parent, model_field))
            model.save()
            model.submit_to_celery()
            return JsonResponse({'valid': True})
        return JsonResponse({'valid': False, 'errors': form.errors})


class DjanguiScriptHome(TemplateView):
    template_name = 'scripts_home.html'

    def get_context_data(self, **kwargs):
        ctx = super(DjanguiScriptHome, self).get_context_data(**kwargs)
        ctx['scripts'] = []
        for model in dir(djangui_models):
            if model == 'DjanguiModel':
                continue
            klass = getattr(djangui_models, model)
            if issubclass(type(klass), ModelBase):
                ctx['scripts'].append({
                    'name': klass.__name__,
                    'objects': klass.objects.all(),
                })
        return ctx