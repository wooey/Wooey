from __future__ import absolute_import, unicode_literals
from collections import defaultdict

from django.views.generic import DetailView, TemplateView
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.forms import FileField
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_text

from django.contrib.contenttypes.models import ContentType

from ..backend import utils
from ..models import WooeyJob, Script, WooeyFile, Favorite
from .. import settings as wooey_settings
from ..django_compat import JsonResponse


class WooeyScriptBase(DetailView):
    model = Script
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    render_fn = None

    def get_context_data(self, **kwargs):
        context = super(WooeyScriptBase, self).get_context_data(**kwargs)

        # returns the models required and optional fields as html
        job_id = self.kwargs.get('job_id')
        initial = None
        if job_id:
            job = WooeyJob.objects.get(pk=job_id)
            # import pdb; pdb.set_trace();
            if job.user is None or (self.request.user.is_authenticated() and job.user == self.request.user):
                initial = defaultdict(list)
                for i in job.get_parameters():
                    value = i.value
                    if value is not None:
                        initial[i.parameter.slug].append(value)

        context['form'] = utils.get_form_groups(model=self.object, initial=initial, render_fn=self.render_fn)
        return context

    def post(self, request, *args, **kwargs):
        post = request.POST.copy()
        user = request.user if request.user.is_authenticated() else None
        if not wooey_settings.WOOEY_ALLOW_ANONYMOUS and user is None:
            return {'valid': False, 'errors': {'__all__': [force_text(_('You are not permitted to access this script.'))]}}

        form = utils.get_master_form(pk=post['wooey_type'])
        # TODO: Check with people who know more if there's a smarter way to do this
        utils.validate_form(form=form, data=post, files=request.FILES)
        # for cloned jobs, we don't have the files in input fields, they'll be in a list like ['', filename]
        # This will cause issues.
        to_delete = []
        for i in post:
            if isinstance(form.fields.get(i), FileField):
                # if we have a value set, reassert this
                new_values = list(filter(lambda x: x, post.getlist(i)))
                cleaned_values = []
                for new_value in new_values:
                    if i not in request.FILES and (i not in form.cleaned_data or (not [j for j in form.cleaned_data[i] if j] and new_value)):
                        # this is a previously set field, so a cloned job
                        if new_value is not None:
                            cleaned_values.append(utils.get_storage(local=False).open(new_value))
                        to_delete.append(i)
                if cleaned_values:
                    form.cleaned_data[i] = cleaned_values
        for i in to_delete:
            if i in form.errors:
                del form.errors[i]

        # because we can have multiple files for a field, we need to update our form.cleaned_data to be a list of files
        for i in request.FILES:
            v = request.FILES.getlist(i)
            if i in form.cleaned_data:
                cleaned = form.cleaned_data[i]
                cleaned = cleaned if isinstance(cleaned, list) else [cleaned]
                if len(cleaned) != len(v):
                    form.cleaned_data[i] = v
                    
        if not form.errors:
            # data = form.cleaned_data
            script_pk = form.cleaned_data.get('wooey_type')
            script = Script.objects.get(pk=script_pk)
            valid = utils.valid_user(script, request.user).get('valid')
            if valid is True:
                group_valid = utils.valid_user(script.script_group, request.user).get('valid')
                if valid is True and group_valid is True:
                    job = utils.create_wooey_job(script_pk=script_pk, user=user, data=form.cleaned_data)
                    job.submit_to_celery()
                    return {'valid': True, 'job_id': job.id}

            return {'valid': False, 'errors': {'__all__': [force_text(_('You are not permitted to access this script.'))]}}

        return {'valid': False, 'errors': form.errors}


class WooeyScriptJSON(WooeyScriptBase):

    # FIXME: the form data is returned as form objects so can be passed to templates
    # this render_fn allows us to pass the return through a stringify method for JSON
    render_fn = lambda form: form.as_table()

    def render_to_response(self, *args, **kwargs):
        data = super(WooeyScriptJSON, self).render_to_response(*args, **kwargs)
        return JsonResponse(data)


    def post(self, *args, **kwargs):
        data = super(WooeyScriptJSON, self).post(*args, **kwargs)
        return JsonResponse(data)

class WooeyScriptView(WooeyScriptBase):

    template_name = 'wooey/scripts/script_view.html'

    def post(self, *args, **kwargs):
        data = super(WooeyScriptView, self).post(*args, **kwargs)
        if data['valid']:
            return HttpResponseRedirect( reverse('wooey:celery_results_info', kwargs={'job_id': data['job_id'] }) )
        else:
            # FIXME: This works but the form handling here should return the submitted data
            # may need to refactor the JSON stuff a little bit to make this work
            return self.get(*args, **kwargs)



class WooeyHomeView(TemplateView):
    template_name = 'wooey/home.html'

    def get_context_data(self, **kwargs):
        #job_id = self.request.GET.get('job_id')
        ctx = super(WooeyHomeView, self).get_context_data(**kwargs)
        ctx['scripts'] = Script.objects.all()


        # Get the id of every favorite (scrapbook) file
        ctype = ContentType.objects.get_for_model(Script)
        ctx['favorite_script_ids'] = Favorite.objects.filter(content_type=ctype, user=self.request.user).values_list('object_id', flat=True)

        return ctx

class WooeyProfileView(TemplateView):
    template_name = 'wooey/profile/profile_base.html'


class WooeyScrapbookView(TemplateView):
    template_name = 'wooey/scrapbook.html'


    def get_context_data(self, **kwargs):
        ctx = super(WooeyScrapbookView, self).get_context_data(**kwargs)

        # Get the id of every favorite (scrapbook) file
        ctype = ContentType.objects.get_for_model(WooeyFile)
        favorite_file_ids = Favorite.objects.filter(content_type=ctype, user=self.request.user).values_list('object_id', flat=True)

        out_files = utils.get_file_previews_by_ids(favorite_file_ids)

        all = out_files.pop('all', [])
        archives = out_files.pop('archives', [])

        ctx['file_groups'] = out_files
        ctx['favorite_file_ids'] = favorite_file_ids

        return ctx