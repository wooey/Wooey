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

from .models import djangui_models
# Create your views here.

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
    success_url = reverse_lazy('{{ app_name }}_home')

class DjanguiScriptJSON(DjanguiScriptMixin, View):
    def get(self, request, *args, **kwargs):
        # returns the models required and optional fields as html
        d = {'action': reverse('djangui_app_script_json', kwargs={'script_name': self.script_name}), 'required': '', 'optional': ''}
        form = modelform_factory(self.model, fields=self.model.get_required_fields(), exclude=('djangui_script_name', 'djangui_celery_id', 'djangui_celery_state'))
        d['required'] = str(form())
        form = modelform_factory(self.model, fields=self.model.get_optional_fields(), exclude=('djangui_script_name', 'djangui_celery_id', 'djangui_celery_state'))
        d['optional'] = str(form())
        return JsonResponse(d)

    def post(self, request, *args, **kwargs):
        pass


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