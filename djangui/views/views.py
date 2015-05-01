from django.views.generic import DetailView, TemplateView, CreateView
from django.http import JsonResponse
from django.conf import settings
from django.forms import FileField
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model, login, authenticate

from djangui.backend import utils
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
                        path = post.get(i)
                        if path:
                            form.cleaned_data[i] = default_storage.open(path)
            for i in to_delete:
                if i in form.errors:
                    del form.errors[i]

        if not form.errors:
            # data = form.cleaned_data
            job, com = form.save()
            job.submit_to_celery(command=com)
            return JsonResponse({'valid': True})

        return JsonResponse({'valid': False, 'errors': form.errors})


class DjanguiHomeView(TemplateView):
    template_name = 'djangui_home.html'

    def get_context_data(self, **kwargs):
        task_id = self.request.GET.get('task_id')
        ctx = super(DjanguiHomeView, self).get_context_data(**kwargs)
        ctx['djangui_scripts'] = getattr(settings, 'DJANGUI_SCRIPTS', {})
        if task_id:
            job = DjanguiJob.objects.get(celery_id=task_id)
            if job.user is None or (self.request.user.is_authenticated() and job.user == self.request.user):
                ctx['clone_job'] = {'task_id': task_id, 'url': job.get_resubmit_url()}
        return ctx

class DjanguiRegister(CreateView):
    template_name = 'registration/register.html'
    model = get_user_model()
    fields = ('username', 'email', 'password')

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if request.POST['password'] != request.POST['password2']:
            form.add_error('password', 'Passwords do not match.')
        if request.POST['username'].lower() == 'admin':
            form.add_error('username', 'Reserved username.')
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        next_url = self.request.POST.get('next')
        # for some bizarre reason the password isn't setting by the modelform
        self.object.set_password(self.request.POST['password'])
        self.object.save()
        auser = authenticate(username=self.object.username, password=self.request.POST['password'])
        login(self.request, auser)
        return reverse(next_url) if next_url else reverse('djangui_home')