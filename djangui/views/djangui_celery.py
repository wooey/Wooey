import os

from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_unicode

from djcelery.models import TaskMeta
from celery import app, states

celery_app = app.app_or_default()

from ..models import DjanguiJob

def celery_status(request):
    jobs = DjanguiJob.objects.filter(user=request.user if request.user.is_authenticated() else None)
    if getattr(settings, 'DJANGUI_CELERY', False):
        # TODO: Batch this to a scheduled task that just updates our DjanguiJob info when done
        tasks = [job.celery_id for job in jobs]
        celery_tasks = dict([(task.task_id, task) for task in TaskMeta.objects.filter(task_id__in=tasks)])
        to_update = []
        for job in jobs:
            celery_task = celery_tasks.get(job.celery_id)
            if celery_task is None and job.celery_state != states.FAILURE:
                continue
                # the task doesn't exist, consider it a failure
                # TODO: we can't report these with all backends, code a way to figure out backend and see if this is viable
                job.celery_state = states.FAILURE
                to_update.append(job)
            elif celery_task is not None and job.celery_state != celery_task.status:
                job.celery_state = celery_task.status
                to_update.append(job)
        for i in to_update:
            i.save()
    return JsonResponse([{'job_name': job.job_name, 'job_status': job.celery_state,
                        'job_submitted': job.created_date.strftime('%b %d %Y, %H:%M:%S'),
                        'job_id': job.pk,
                        'job_url': reverse('celery_results_info', kwargs={'job_id': job.pk})} for job in jobs], safe=False)


def celery_task_command(request):
    command = request.POST.get('celery-command')
    task_id = request.POST.get('task-id')
    job = DjanguiJob.objects.get(celery_id=task_id)
    user = None if not request.user.is_authenticated() and settings.DJANGUI_ALLOW_ANONYMOUS else request.user
    response = {'valid': False,}
    if user == job.user:
        if command == 'resubmit':
            job.submit_to_celery(resubmit=True)
            response.update({'valid': True, 'extra': {'task_url': reverse('celery_results_info', kwargs={'task_id': job.celery_id})}})
        elif command == 'clone':
            response.update({'valid': True, 'redirect': '{0}?task_id={1}'.format(reverse('djangui_task_launcher'), task_id)})
        elif command == 'delete':
            job.delete()
            response.update({'valid': True, 'redirect': reverse('djangui_home')})
        elif command == 'stop':
            celery_app.control.revoke(task_id, terminate=True)
            response.update({'valid': True, 'redirect': reverse('celery_results_info', kwargs={'task_id': task_id})})
        else:
            response.update({'errors': {'__all__': force_unicode(_("Unknown Command"))}})
    return JsonResponse(response)


class CeleryTaskView(TemplateView):
    template_name = 'tasks/task_view.html'

    @staticmethod
    def get_file_fields(model):
        parameters = model.get_parameters()
        files = []
        for field in parameters:
            try:
                if field.parameter.form_field == 'FileField':
                    d = {'name': field.parameter.slug}
                    value = field.value
                    if value is None:
                        continue
                    d['url'] = value.url
                    d['path'] = value.path
                    files.append(d)
            except ValueError:
                continue

        known_files = {i['url'] for i in files}
        # add the user_output files, these are things which may be missed by the model fields because the script
        # generated them without an explicit argument reference in argparse
        file_groups = {'archives': []}
        absbase = os.path.join(settings.MEDIA_ROOT, model.user.username if model.user is not None else '', model.save_path)
        for filename in os.listdir(absbase):
            url = '/'.join([model.user.username if model.user is not None else '', model.save_path, filename])
            if url in known_files:
                continue
            d = {'name': filename, 'path': os.path.join(absbase, filename), 'url': '{0}{1}'.format(settings.MEDIA_URL, url)}
            if filename.startswith('djangui_all'):
                file_groups['archives'].append(d)
            else:
                files.append(d)

        # establish grouping by inferring common things
        file_groups['all'] = files
        import imghdr
        file_groups['images'] = [{'name': filemodel['name'], 'url': filemodel['url']} for filemodel in files if imghdr.what(filemodel.get('path', filemodel['url']))]
        file_groups['tabular'] = []
        file_groups['fasta'] = []

        def test_delimited(filepath):
            import csv
            with open(filepath, 'rb') as csv_file:
                try:
                    dialect = csv.Sniffer().sniff(csv_file.read(1024*16), delimiters=',\t')
                except Exception as e:
                    return False, None
                csv_file.seek(0)
                reader = csv.reader(csv_file, dialect)
                rows = []
                try:
                    for index, entry in enumerate(reader):
                        if index == 5:
                            break
                        rows.append(entry)
                except Exception as e:
                    return False, None
                return True, rows

        def test_fastx(filepath):
            # if every odd line starts with a >, it's a fasta
            # if every first line starts with a > and every third a +, it's a fastq
            with open(filepath, 'rb') as fastx_file:
                rows = []
                for row_index, row in enumerate(fastx_file, 1):
                    if row_index > 28:
                        break
                    if row_index % 4 == 0:
                        pass
                    elif row_index % 3 == 0:
                        # check for both fastq/a
                        if not row[0] == '+' or row[0] == '>':
                            return False, None
                    elif row_index % 2 == 0:
                        pass
                    else:
                        if not row[0] == '>':
                            return False, None
                    rows.append(row)
            return True, rows

        for filemodel in files:
            is_delimited, first_rows = test_delimited(filemodel.get('path', filemodel['url']))
            if is_delimited:
                file_groups['tabular'].append({'name': filemodel['name'], 'preview': first_rows, 'url': filemodel['url']})
            else:
                is_fasta, first_rows = test_fastx(filemodel.get('path', filemodel['url']))
                if is_fasta:
                    file_groups['fasta'].append({'name': filemodel['name'], 'preview': first_rows, 'url': filemodel['url']})
        return file_groups

    def get_context_data(self, **kwargs):
        ctx = super(CeleryTaskView, self).get_context_data(**kwargs)
        task_id = ctx.get('job_id')
        djangui_job = DjanguiJob.objects.get(pk=task_id)
        ctx['task_info'] = {'stdout': '', 'stderr': '', 'job_id': djangui_job.celery_id,
                            'status': djangui_job.celery_state, 'submission_time': djangui_job.created_date,
                            'last_modified': djangui_job.modified_date, 'job_name': djangui_job.job_name,
                            'job_command': djangui_job.command,
                            'job_description': djangui_job.job_description, 'all_files': {},
                            'file_groups': {}}
        out_files = self.get_file_fields(djangui_job)
        all = out_files.pop('all')
        archives = out_files.pop('archives')
        ctx['task_info'].update({
                'all_files': all,
                'archives': archives,
                'file_groups': out_files,
            })
        # if celery_task:
        #     try:
        #         stdout, stderr = celery_task.result
        #     except KeyError:
        #         stdout, stderr = None, None
        #     ctx['task_info'].update({
        #         'stdout': stdout,
        #         'stderr': stderr,
        #         'status': celery_task.status,
        #         'last_modified': celery_task.date_done,
        #     })
        return ctx

