from __future__ import absolute_import
import os

from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_unicode
from django.db.models import Q

from djcelery.models import TaskMeta
from celery import app, states

celery_app = app.app_or_default()

from ..models import DjanguiJob
from .. import settings as djangui_settings

def celery_status(request):
    spanbase = "<span class='glyphicon {}' data-toggle='tooltip' data-trigger='hover' title='{}'></span>"
    STATE_MAPPER = {
        DjanguiJob.COMPLETED: spanbase.format('glyphicon-ok', _('Success')),
        DjanguiJob.RUNNING: spanbase.format('glyphicon-refresh spinning', _('Executing')),
        states.PENDING: spanbase.format('glyphicon-time', _('In queue')),
        states.REVOKED: spanbase.format('glyphicon-stop', _('Halted')),
        DjanguiJob.SUBMITTED: spanbase.format('glyphicon-hourglass', _('Waiting to be queued'))
    }
    jobs = DjanguiJob.objects.filter(Q(user=None) | Q(user=request.user) if request.user.is_authenticated() else Q(user=None))
    jobs = jobs.exclude(status=DjanguiJob.DELETED)
    # divide into user and anon jobs
    def get_job_list(job_query):
        return [{'job_name': job.job_name, 'job_status': STATE_MAPPER.get(job.status, job.status),
                'job_submitted': job.created_date.strftime('%b %d %Y, %H:%M:%S'),
                'job_id': job.pk, 'job_description': 'Script: {}\n{}'.format(job.script.script_name, job.job_description),
                'job_url': reverse('celery_results_info', kwargs={'job_id': job.pk})} for job in job_query]
    d = {'user': get_job_list([i for i in jobs if i.user == request.user]),
         'anon': get_job_list([i for i in jobs if i.user == None])}
    return JsonResponse(d, safe=False)


def celery_task_command(request):

    command = request.POST.get('celery-command')
    job_id = request.POST.get('job-id')
    job = DjanguiJob.objects.get(pk=job_id)
    from ..backend.utils import valid_user
    response = {'valid': False,}
    valid = valid_user(job.script, request.user)
    if valid.get('valid') is True:
        user = request.user if request.user.is_authenticated() else None
        if user == job.user or job.user == None:
            if command == 'resubmit':
                new_job = job.submit_to_celery(resubmit=True, user=request.user)
                response.update({'valid': True, 'extra': {'task_url': reverse('celery_results_info', kwargs={'job_id': new_job.pk})}})
            elif command == 'clone':
                response.update({'valid': True, 'redirect': '{0}?job_id={1}'.format(reverse('djangui_task_launcher'), job_id)})
            elif command == 'delete':
                job.status = DjanguiJob.DELETED
                job.save()
                response.update({'valid': True, 'redirect': reverse('djangui_home')})
            elif command == 'stop':
                celery_app.control.revoke(job.celery_id, signal='SIGKILL', terminate=True)
                job.status = states.REVOKED
                job.save()
                response.update({'valid': True, 'redirect': reverse('celery_results_info', kwargs={'job_id': job_id})})
            else:
                response.update({'errors': {'__all__': [force_unicode(_("Unknown Command"))]}})
    else:
        response.update({'errors': {'__all__': [force_unicode(valid.get('error'))]}})
    return JsonResponse(response)


class CeleryTaskView(TemplateView):
    template_name = 'tasks/task_view.html'

    def get_context_data(self, **kwargs):
        ctx = super(CeleryTaskView, self).get_context_data(**kwargs)
        job_id = ctx.get('job_id')
        djangui_job = DjanguiJob.objects.get(pk=job_id)
        ctx['task_info'] = {'stdout': '', 'stderr': '', 'job': djangui_job,
                            'all_files': {},
                            'file_groups': {}}
        from ..backend import utils
        out_files = utils.get_file_previews(djangui_job)
        all = out_files.pop('all', [])
        archives = out_files.pop('archives', [])
        ctx['task_info'].update({
                'all_files': all,
                'archives': archives,
                'file_groups': out_files,
                'status': djangui_job.status,
                'last_modified': djangui_job.modified_date,
            })
        return ctx

