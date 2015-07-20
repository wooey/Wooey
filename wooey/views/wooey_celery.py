from __future__ import absolute_import
import os
import six

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_text
from django.db.models import Q
from django.template.defaultfilters import escape

from djcelery.models import TaskMeta
from celery import app, states

celery_app = app.app_or_default()

from ..models import WooeyJob
from .. import settings as wooey_settings
from ..backend.utils import valid_user, get_file_previews
from ..django_compat import JsonResponse
from django.db.models import Q

SPANBASE = "<span title='{}' class='glyphicon {}'></span> "
STATE_MAPPER = {
    #  Default Primary Success Info Warning Danger
    WooeyJob.COMPLETED: SPANBASE.format(_('Success'), 'success glyphicon-ok'),
    WooeyJob.RUNNING: SPANBASE.format(_('Executing'), 'success glyphicon-refresh spinning'),
    states.PENDING: SPANBASE.format(_('Queued'), 'glyphicon-time'),
    states.REVOKED: SPANBASE.format(_('Halted'), 'danger glyphicon-stop'),
    states.FAILURE: SPANBASE.format(_('Failure'), 'danger glyphicon-exclamation-sign'),
    WooeyJob.SUBMITTED: SPANBASE.format(_('Waiting'), 'glyphicon-hourglass'),
}



def generate_job_list(job_query):

    if job_query is None:
        return []

    jobs = []

    for job in job_query:
        jobs.append({
            'id': job.pk,
            'name': escape(job.job_name),
            'description': escape(six.u('Script: {}\n{}').format(job.script.script_name, job.job_description)),
            'url': reverse('wooey:celery_results_info', kwargs={'job_id': job.pk}),
            'submitted': job.created_date.strftime('%b %d %Y, %H:%M:%S'),
            'status': STATE_MAPPER.get(job.status, job.status),
        })
    return jobs

def get_global_queue(request):
    jobs = WooeyJob.objects.filter( Q(status=WooeyJob.RUNNING) | Q(status=WooeyJob.SUBMITTED) )
    return jobs

def global_queue_json(request):
    jobs = get_global_queue(request)
    return JsonResponse(generate_job_list(jobs), safe=False)

def get_user_queue(request):
    user = request.user
    jobs = WooeyJob.objects.filter(Q(user=None) | Q(user=user) if request.user.is_authenticated() else Q(user=None))
    jobs = jobs.exclude(Q(status=WooeyJob.DELETED) | Q(status=WooeyJob.COMPLETED))
    return jobs

def user_queue_json(request):
    jobs = get_user_queue(request)
    return JsonResponse(generate_job_list(jobs), safe=False)

def get_user_results(request):
    user = request.user
    jobs = WooeyJob.objects.filter(Q(status=WooeyJob.COMPLETED) & ( Q(user=None) | Q(user=user) if request.user.is_authenticated() else Q(user=None)) )
    jobs = jobs.exclude(status=WooeyJob.DELETED)
    return jobs

def user_results_json(request):
    jobs = get_user_results(request)
    return JsonResponse(generate_job_list(jobs), safe=False)

def all_queues_json(request):
    return JsonResponse({
        'global': generate_job_list(get_global_queue(request)),
        'user': generate_job_list(get_user_queue(request)),
        'results': generate_job_list(get_user_results(request)),
    }, safe=False)



def celery_status(request):

    user = request.user
    if user.is_superuser:
        jobs = WooeyJob.objects.all()
        jobs = jobs.exclude(status=WooeyJob.DELETED)
    else:
        jobs = WooeyJob.objects.filter(Q(user=None) | Q(user=user) if request.user.is_authenticated() else Q(user=None))
        jobs = jobs.exclude(status=WooeyJob.DELETED)
    # divide into user and anon jobs
    d = {'user': get_job_list([i for i in jobs if i.user == user]),
         'anon': get_job_list([i for i in jobs if i.user == None or (user.is_superuser and i.user != user)])}
    return JsonResponse(d, safe=False)


def celery_task_command(request):

    command = request.POST.get('celery-command')
    job_id = request.POST.get('job-id')
    job = WooeyJob.objects.get(pk=job_id)
    response = {'valid': False,}
    valid = valid_user(job.script, request.user)
    if valid.get('valid') is True:
        user = request.user if request.user.is_authenticated() else None
        if user == job.user or job.user == None:
            if command == 'resubmit':
                new_job = job.submit_to_celery(resubmit=True, user=request.user)
                response.update({'valid': True, 'extra': {'task_url': reverse('wooey:celery_results_info', kwargs={'job_id': new_job.pk})}})
            elif command == 'rerun':
                job.submit_to_celery(user=request.user, rerun=True)
                response.update({'valid': True, 'redirect': reverse('wooey:celery_results_info', kwargs={'job_id': job_id})})
            elif command == 'clone':
                response.update({'valid': True, 'redirect': '{0}?job_id={1}'.format(reverse('wooey:wooey_task_launcher'), job_id)})
            elif command == 'delete':
                job.status = WooeyJob.DELETED
                job.save()
                response.update({'valid': True, 'redirect': reverse('wooey:wooey_home')})
            elif command == 'stop':
                celery_app.control.revoke(job.celery_id, signal='SIGKILL', terminate=True)
                job.status = states.REVOKED
                job.save()
                response.update({'valid': True, 'redirect': reverse('wooey:celery_results_info', kwargs={'job_id': job_id})})
            else:
                response.update({'errors': {'__all__': [force_text(_("Unknown Command"))]}})
    else:
        response.update({'errors': {'__all__': [force_text(valid.get('error'))]}})
    return JsonResponse(response)


class CeleryTaskView(TemplateView):
    template_name = 'wooey/tasks/task_view.html'

    def get_context_data(self, **kwargs):
        ctx = super(CeleryTaskView, self).get_context_data(**kwargs)
        job_id = ctx.get('job_id')
        try:
            wooey_job = WooeyJob.objects.get(pk=job_id)
        except WooeyJob.DoesNotExist:
            ctx['task_error'] = _('This task does not exist.')
        else:
            user = self.request.user
            user = None if not user.is_authenticated() and wooey_settings.WOOEY_ALLOW_ANONYMOUS else user
            job_user = wooey_job.user
            if job_user == None or job_user == user or (user != None and user.is_superuser):
                out_files = get_file_previews(wooey_job)
                all = out_files.pop('all', [])
                archives = out_files.pop('archives', [])
                ctx['task_info'] = {
                        'all_files': all,
                        'archives': archives,
                        'file_groups': out_files,
                        'status': wooey_job.status,
                        'last_modified': wooey_job.modified_date,
                        'job': wooey_job
                    }
            else:
                ctx['task_error'] = _('You are not authenticated to view this job.')
        return ctx

