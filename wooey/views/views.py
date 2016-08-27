from __future__ import absolute_import, unicode_literals
from collections import defaultdict
import datetime as dt

from django.views.generic import DetailView, TemplateView, View
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.forms import FileField
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.template import RequestContext
from django.contrib.auth import get_user_model
from django.http import Http404

from django.contrib.contenttypes.models import ContentType

from ..backend import utils
from ..models import WooeyJob, Script, UserFile, Favorite, ScriptVersion
from .. import settings as wooey_settings
from ..django_compat import JsonResponse


class WooeyScriptBase(DetailView):
    model = Script
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    @staticmethod
    def render_fn(s):
        return s

    def get_object(self, queryset=None):
        script_version = self.kwargs.get('script_verison')
        script_iteration = self.kwargs.get('script_iteration')
        if script_version is not None:
            if queryset is None:
                queryset = self.get_queryset()

            slug = self.kwargs.get(self.slug_url_kwarg, None)

            # Next, try looking up by slug.
            if slug is not None:
                slug_field = self.get_slug_field()
                queryset = queryset.filter(**{slug_field: slug, 'script_version': script_version})
                if script_iteration:
                    queryset.filter(script_iteration=script_iteration)
                else:
                    queryset.latest('script_iteration')
            else:
                raise AttributeError("Generic detail view %s must be called with "
                                     "either an object pk or a slug."
                                     % self.__class__.__name__)
            try:
                # Get the single item from the filtered queryset
                obj = queryset.get()
            except queryset.model.DoesNotExist:
                raise Http404(_("No %(verbose_name)s found matching the query") %
                              {'verbose_name': queryset.model._meta.verbose_name})
            return obj
        else:
            return super(WooeyScriptBase, self).get_object(queryset=queryset)

    def get_context_data(self, **kwargs):
        context = super(WooeyScriptBase, self).get_context_data(**kwargs)

        # returns the models required and optional fields as html
        job_id = self.kwargs.get('job_id')
        initial = defaultdict(list)

        if job_id:
            job = WooeyJob.objects.get(pk=job_id)
            if job.user is None or (self.request.user.is_authenticated() and job.user == self.request.user):
                context['job_info'] = {'job_id': job_id, 'url': job.get_resubmit_url(), 'data_url': job.script_version.script.get_url()}

                for i in job.get_parameters():
                    value = i.value
                    if value is not None:
                        initial[i.parameter.slug].append(value)

        context['form'] = utils.get_form_groups(script_version=self.object.latest_version, initial_dict=initial, render_fn=self.render_fn, pk=self.object.pk)
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
                    if i not in request.FILES and (i not in form.cleaned_data or (new_value and (form.cleaned_data[i] is None or not [j for j in form.cleaned_data[i] if j]))):
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
                form.cleaned_data[i] = list(set(cleaned).union(set(v)))

        if not form.errors:
            # data = form.cleaned_data
            version_pk = form.cleaned_data.get('wooey_type')
            script_version = ScriptVersion.objects.get(pk=version_pk)
            valid = utils.valid_user(script_version.script, request.user).get('valid')
            if valid == True:
                group_valid = utils.valid_user(script_version.script.script_group, request.user).get('valid')
                if valid == True and group_valid == True:
                    job = utils.create_wooey_job(script_version_pk=version_pk, user=user, data=form.cleaned_data)
                    job.submit_to_celery()
                    return {'valid': True, 'job_id': job.id}

            return {'valid': False, 'errors': {'__all__': [force_text(_('You are not permitted to access this script.'))]}}

        return {'valid': False, 'errors': form.errors}


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

    template_name = 'wooey/scripts/script_view.html'

    def post(self, *args, **kwargs):
        data = super(WooeyScriptView, self).post(*args, **kwargs)
        if data['valid']:
            data['redirect'] = reverse('wooey:celery_results', kwargs={'job_id': data['job_id']})
        return JsonResponse(data)


class WooeyHomeView(TemplateView):
    template_name = 'wooey/home.html'

    def get_context_data(self, **kwargs):
        #job_id = self.request.GET.get('job_id')
        ctx = super(WooeyHomeView, self).get_context_data(**kwargs)
        ctx['scripts'] = utils.get_current_scripts()

        # Check for logged in user
        if self.request.user.is_authenticated():
            # Get the id of every favorite (scrapbook) file
            ctype = ContentType.objects.get_for_model(Script)
            ctx['favorite_script_ids'] = Favorite.objects.filter(content_type=ctype, user__id=self.request.user.id).values_list('object_id', flat=True)
        else:
            ctx['favorite_script_ids'] = []

        return ctx


class WooeyProfileView(TemplateView):
    template_name = 'wooey/profile/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super(WooeyProfileView, self).get_context_data(**kwargs)

        if 'username' in self.kwargs:
            user = get_user_model()
            ctx['profile_user'] = user.objects.get(username=self.kwargs.get('username'))

        else:
            if self.request.user and self.request.user.is_authenticated():
                ctx['profile_user'] = self.request.user

        return ctx


class WooeyScrapbookView(TemplateView):
    template_name = 'wooey/scrapbook.html'

    def get_context_data(self, **kwargs):
        ctx = super(WooeyScrapbookView, self).get_context_data(**kwargs)

        # Get the id of every favorite (scrapbook) file
        ctype = ContentType.objects.get_for_model(UserFile)
        favorite_file_ids = Favorite.objects.filter(content_type=ctype, user=self.request.user).values_list('object_id', flat=True)

        out_files = utils.get_file_previews_by_ids(favorite_file_ids)

        all = out_files.pop('all', [])
        archives = out_files.pop('archives', [])

        ctx['file_groups'] = out_files
        ctx['favorite_file_ids'] = favorite_file_ids

        return ctx


class WooeySearchBase(View):

    model = None
    search_fields = []

    def get(self, request, *args, **kwargs):

        self.search_results = None
        if 'q' in request.GET:
            query_string = request.GET['q'].strip()

            query = utils.get_query(query_string, self.search_fields)
            self.search_results = self.model.objects.filter(query)

            return self.search(request, *args, **kwargs)


class WooeyScriptSearchBase(WooeySearchBase):

    model = Script
    search_fields = ['script_name', 'script_description']


class WooeyScriptSearchJSON(WooeyScriptSearchBase):
    """
    Returns the result of the script search as JSON containing data only
    """

    def search(self, request):
        results = []
        for script in self.search_results:
            results.append({
                'id': script.id,
                'name': script.script_name,
                'description': script.script_description,
                'url': reverse('wooey:wooey_script', kwargs={'slug': script.slug}),
            })
        return JsonResponse({'results': results})


class WooeyScriptSearchJSONHTML(WooeyScriptSearchBase):
    """
    Returns the result of the script search as JSON containing rendered template
    elements for display in the original page. This is a temporary function
    until the handling is moved to client side rendering.
    """

    def search(self, request):
        results = []
        for script in self.search_results:
            results.append(render_to_string('wooey/scripts/script_panel.html', {'script': script}, context_instance=RequestContext(request)))
        return JsonResponse({'results': results})
