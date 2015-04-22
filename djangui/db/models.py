__author__ = 'chris'
import os
import errno
import importlib

from django.db import models
from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# TODO: Remove the coupling of this with djguicore
from djguicore.models import DjanguiJob
# TODO: Handle cases where celery is not used
tasks = importlib.import_module(settings.DJANGUI_CELERY_TASKS)

def get_script_options(model):
    script_options = dict([(i.name, getattr(model, i.name)) for i in model._meta.fields])
    com = [script_options.pop('djangui_script_name')]
    script_options.pop('djangui_celery_id')
    script_options.pop('djangui_celery_state')
    cwd = ''
    for i, v in script_options.iteritems():
        param = model.get_option_param(i)
        if param is None:
            continue
        if isinstance(v, FieldFile):
            try:
                if not default_storage.exists(v.path):
                    # create the file we're writing to
                    # To handle zipping files, and access to files not explicitly referenced in the script,
                    # we make a directory for each job.
                    if not cwd:
                        cwd = os.path.join(model.djangui_output_path, str(DjanguiJob.objects.count()))
                    getattr(model, i).save(cwd, ContentFile(''))
            except ValueError:
                getattr(model, i).save(model.get_output_default(i), ContentFile(''))
            com += [param, v.path]
        else:
            if str(v) == 'True':
                com += [param]
            elif str(v) == 'False':
                continue
            else:
                if v:
                    com += [param, str(v)]
    return com, cwd

class DjanguiModel(models.Model):
    # blank=True, null=True is to allow anonymous users to submit jobs
    # TODO: add a setting for allowing anonymous users
    djangui_user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    djangui_job_name = models.CharField(max_length=255)
    djangui_job_description = models.TextField()
    djangui_command = models.TextField(null=True, blank=True)
    djangui_celery_id = models.CharField(max_length=255, blank=True, null=True)
    djangui_celery_state = models.CharField(max_length=255, blank=True, null=True)
    djangui_save_path = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def get_option_param(self, param):
        # returns the param argparse accepts (ie --p vs -p)
        return self.djangui_options.get(param)

    def get_output_default(self, param):
        try:
            return self._djangui_temp_output[param]
        except (KeyError, AttributeError) as e:
            return self.djangui_output_options.get(param)

    @classmethod
    def get_required_fields(cls):
        return [i.name for i in cls._meta.fields if i.name in cls.djangui_options and i.name not in cls.optional_fields or i.blank is False]

    @classmethod
    def get_optional_fields(cls):
        return cls.optional_fields.intersection([i.name for i in cls._meta.fields])-set(cls.get_required_fields())

    @classmethod
    def get_class_name(cls):
        return cls.__class__.__name__

    def submit_to_celery(self, resubmit=False):
        script_options, cwd = get_script_options(self)
        if not cwd:
            folder = os.path.join(self.djangui_output_path, str(DjanguiJob.objects.count()))
        else:
            folder = cwd
        cwd = os.path.join(settings.MEDIA_ROOT, folder)
        abscwd = os.path.abspath(cwd)
        try:
            os.makedirs(abscwd)
        except OSError as exc:
            # directory already exists
            if exc.errno == errno.EEXIST and os.path.isdir(abscwd):
                pass
            else:
                raise
        results = tasks.submit_script.delay(script_options, djangui_cwd=abscwd)
        if resubmit:
            # this is a method(hack) to clone ourselves and create a new object
            self.pk = None
        self.djangui_save_path = folder
        self.djangui_celery_id = results.id
        self.djangui_celery_state = results.state
        self.djangui_command = ' '.join(script_options)
        self.save()
        job = DjanguiJob(djangui_celery_id=self.djangui_celery_id, djangui_user=self.djangui_user, content_object=self)
        job.save()
        return self