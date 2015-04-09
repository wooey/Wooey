import sys

from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.db.models.base import ModelBase
from django.views.generic import CreateView, UpdateView, TemplateView

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


class DjanguiScriptEdit(DjanguiScriptMixin, UpdateView):
    template_name = 'generic_script_view.html'
    fields = '__all__'


class DjanguiScriptCreate(DjanguiScriptMixin, CreateView):
    fields = '__all__'
    template_name = 'generic_script_create.html'
    success_url = reverse_lazy('{{ app_name }}_home')


class DjanguiScriptHome(TemplateView):
    template_name = 'scripts_home.html'

    def get_context_data(self, **kwargs):
        ctx = super(DjanguiScriptHome, self).get_context_data(**kwargs)
        ctx['scripts'] = []
        for model in dir(djangui_models):
            klass = getattr(djangui_models, model)
            if issubclass(type(klass), ModelBase):
                ctx['scripts'].append({
                    'name': klass.__name__,
                    'objects': klass.objects.all(),
                })
        return ctx