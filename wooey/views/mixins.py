# __author__ = 'chris'
# from django.views.generic import CreateView, UpdateView
# from django.forms import modelform_factory
# from django.core.urlresolvers import reverse_lazy
# from django.conf import settings
#
#
# class WooeyScriptMixin(object):
#     def dispatch(self, request, *args, **kwargs):
#         import pdb; pdb.set_trace();
#         self.script_name = kwargs.pop('script_name', None)
#         if not self.script_name:
#             return super(WooeyScriptMixin, self).dispatch(request, *args, **kwargs)
#         klass = getattr(self.wooey_models, self.script_name)
#         self.model = klass
#         return super(WooeyScriptMixin, self).dispatch(request, *args, **kwargs)
#
#     def get_queryset(self):
#         klass = getattr(self.wooey_models, self.script_name)
#         return klass.objects.all()
#
#     def get_context_data(self, **kwargs):
#         ctx = super(WooeyScriptMixin, self).get_context_data(**kwargs)
#         ctx['script_name'] = self.script_name
#         return ctx
#
#     def get_form_class(self):
#         return modelform_factory(self.model, fields=self.fields, exclude=('wooey_script_name', 'wooey_celery_id', 'wooey_celery_state'))
#
#
# class WooeyScriptEdit(WooeyScriptMixin, UpdateView):
#     template_name = 'generic_script_view.html'
#
#
# class WooeyScriptCreate(WooeyScriptMixin, CreateView):
#     template_name = 'generic_script_create.html'
#
#     def get_success_url(self):
#         return reverse_lazy(getattr(settings, 'POST_SCRIPT_URL', '{}_home'.format(self.app_name)))
#
#     def get_form_class(self):
#         return modelform_factory(self.model, fields=self.fields, exclude=('wooey_user', 'wooey_script_name', 'wooey_celery_id', 'wooey_celery_state'))
#
