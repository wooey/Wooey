from __future__ import absolute_import
__author__ = 'chris'
import os
import errno
import importlib
import json

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils.text import get_valid_filename

from autoslug import AutoSlugField

from celery import states

from .. import settings as djangui_settings
from .. backend import utils

from . mixins import UpdateScriptsMixin, ModelDiffMixin


# TODO: Handle cases where celery is not setup but specified to be used
tasks = importlib.import_module(djangui_settings.DJANGUI_CELERY_TASKS)

class ScriptGroup(UpdateScriptsMixin, models.Model):
    """
        This is a group of scripts, it holds general information
        about a collection of scripts, and allows for custom descriptions

    """
    group_name = models.TextField()
    slug = AutoSlugField(populate_from='group_name', unique=True)
    group_description = models.TextField(null=True, blank=True)
    group_order = models.SmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    user_groups = models.ManyToManyField(Group, blank=True)

    def __unicode__(self):
        return unicode(self.group_name)

class Script(ModelDiffMixin, models.Model):
    script_name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='script_name', unique=True)
    script_group = models.ForeignKey('ScriptGroup')
    script_description = models.TextField(blank=True, null=True)
    script_order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    user_groups = models.ManyToManyField(Group, blank=True)
    script_path = models.FileField()
    execute_full_path = models.BooleanField(default=True) # use full path for subprocess calls
    save_path = models.CharField(max_length=255, blank=True, null=True,
                                 help_text='By default save to the script name,'
                                           ' this will change the output folder.')
    # when a script updates, increment this to keep old scripts that are cloned working. The downside is we get redundant
    # parameters, but even a huge site may only have a few thousand parameters to query though.
    script_version = models.PositiveSmallIntegerField(default=0)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return unicode(self.script_name)

    def get_url(self):
        return reverse('djangui_script', kwargs={'script_group': self.script_group.slug,
                                                      'script_name': self.slug})

    def get_script_path(self):
        path = self.script_path.path
        return path if self.execute_full_path else os.path.split(path)[1]

    @transaction.atomic
    def save(self, **kwargs):
        if 'script_path' in self.changed_fields:
            self.script_version += 1
        new_script = self.pk is None or 'script_path' in self.changed_fields
        # if uploading from the admin, fix its path
        # we do this to avoid having migrations specific to various users with different DJANGUI_SCRIPT_DIR settings
        if new_script or djangui_settings.DJANGUI_SCRIPT_DIR not in self.script_path.file.name:
            new_name = os.path.join(djangui_settings.DJANGUI_SCRIPT_DIR, self.script_path.file.name)
            utils.get_storage(local=False).save(new_name, self.script_path.file)
            # save it locally a well
            if not utils.get_storage(local=True).exists(new_name):
                utils.get_storage(local=True).save(new_name, self.script_path.file)
            self.script_path.save(new_name, self.script_path.file, save=False)
            self.script_path.name = new_name
        super(Script, self).save(**kwargs)
        if new_script:
            if getattr(self, '_add_script', True):
                added, error = utils.add_djangui_script(script=self, group=self.script_group)
                if added is False:
                    # TODO: Make a better error
                    raise BaseException(error)
        utils.load_scripts()



class DjanguiJob(models.Model):
    """
    This model serves to link the submitted celery tasks to a script submitted
    """
    # blank=True, null=True is to allow anonymous users to submit jobs
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    celery_id = models.CharField(max_length=255, null=True)
    job_name = models.CharField(max_length=255)
    job_description = models.TextField(null=True, blank=True)
    stdout = models.TextField(null=True, blank=True)
    stderr = models.TextField(null=True, blank=True)

    DELETED = 'deleted'
    SUBMITTED = 'submitted'
    COMPLETED = 'completed'
    RUNNING = 'running'

    STATUS_CHOICES = (
        (SUBMITTED, _('Submitted')),
        (RUNNING, _('Running')),
        (COMPLETED, _('Completed')),
        (DELETED, _('Deleted')),
    )

    status = models.CharField(max_length=255, default=SUBMITTED, choices=STATUS_CHOICES)

    save_path = models.CharField(max_length=255, blank=True, null=True)
    command = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    script = models.ForeignKey('Script')

    def __unicode__(self):
        return unicode(self.job_name)

    def get_parameters(self):
        return ScriptParameters.objects.filter(job=self)

    def submit_to_celery(self, **kwargs):
        if kwargs.get('resubmit'):
            params = self.get_parameters()
            self.pk = None
            self.save()
            with transaction.atomic():
                for param in params:
                    param.pk = None
                    param.job = self
                    param.recreate()
                    param.save()
        self.status = self.SUBMITTED
        self.save()
        if djangui_settings.DJANGUI_CELERY:
            results = tasks.submit_script.delay(djangui_job=self.pk)
        else:
            results = tasks.submit_script(djangui_job=self.pk)
        return self

    def get_resubmit_url(self):
        return reverse('djangui_script_clone', kwargs={'script_group': self.script.script_group.slug,
                                                      'script_name': self.script.slug, 'job_id': self.pk})

    @staticmethod
    def mkdirs(path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def get_output_path(self):
        path = os.path.join(djangui_settings.DJANGUI_FILE_DIR, get_valid_filename(self.user.username if self.user is not None else ''),
                            get_valid_filename(self.script.slug if not self.script.save_path else self.script.save_path), str(self.pk))
        self.mkdirs(os.path.join(settings.MEDIA_ROOT, path))
        return path

    def get_upload_path(self):
        path = os.path.join(djangui_settings.DJANGUI_FILE_DIR, get_valid_filename(self.user.username if self.user is not None else ''),
                            get_valid_filename(self.script.slug if not self.script.save_path else self.script.save_path))
        self.mkdirs(os.path.join(settings.MEDIA_ROOT, path))
        return path


class ScriptParameterGroup(UpdateScriptsMixin, models.Model):
    group_name = models.TextField()
    script = models.ForeignKey('Script')

    def __unicode__(self):
        return unicode('{}: {}'.format(self.script.script_name, self.group_name))


class ScriptParameter(UpdateScriptsMixin, models.Model):
    """
        This holds the parameter mapping for each script, and enforces uniqueness by each script via a FK.
    """
    script = models.ForeignKey('Script')
    short_param = models.CharField(max_length=255)
    script_param = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='script_param', unique=True)
    is_output = models.BooleanField(default=None)
    required = models.BooleanField(default=False)
    output_path = models.FilePathField(path=settings.MEDIA_ROOT, allow_folders=True, allow_files=False,
                                       recursive=True, max_length=255)
    choices = models.CharField(max_length=255, null=True, blank=True)
    choice_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    form_field = models.CharField(max_length=255)
    default = models.CharField(max_length=255, null=True, blank=True)
    input_type = models.CharField(max_length=255)
    param_help = models.TextField(verbose_name='help', null=True, blank=True)
    is_checked = models.BooleanField(default=False)
    parameter_group = models.ForeignKey('ScriptParameterGroup')

    def __unicode__(self):
        return unicode('{}: {}'.format(self.script.script_name, self.script_param))


# TODO: find a better name for this class
class ScriptParameters(models.Model):
    """
        This holds the actual parameters sent with the submission
    """
    # the details of the actual executed scripts
    job = models.ForeignKey('DjanguiJob')
    parameter = models.ForeignKey('ScriptParameter')
    # we store a JSON dumped string in here to attempt to keep our types in order
    _value = models.TextField(db_column='value')

    BOOLEAN = 'BooleanField'
    CHAR = 'CharField'
    CHOICE = 'ChoiceField'
    FILE = 'FileField'
    FLOAT = 'FloatField'
    INTEGER = 'IntegerField'

    DJANGUI_FIELD_MAP = {
        BOOLEAN: lambda x: str(x).lower() == 'true',
        CHAR: str,
        CHOICE: str,
        FILE: file,
        FLOAT: float,
        INTEGER: int,
    }

    def __unicode__(self):
        return unicode('{}: {}'.format(self.parameter.script_param, self.value))

    def get_subprocess_value(self):
        value = self.value
        if self.value is None:
            return []
        field = self.parameter.form_field
        param = self.parameter.short_param
        if field == self.BOOLEAN:
            if value:
                return [param]
        if field == self.FILE:
            if self.parameter.is_output:
                try:
                    value = value.path
                except AttributeError:
                    value = utils.get_storage(local=True).path(value)
                    # trim the output path, we don't want to be adding our platform specific paths to the output
                    op = self.job.get_output_path()
                    value = value[value.find(op)+len(op)+1:]
            else:
                # make sure we have it locally otherwise download it
                if not utils.get_storage(local=True).exists(value.path):
                    new_path = utils.get_storage(local=True).save(value.path, value)
                    value = new_path
                else:
                    # return the string for processing
                    value = value.path
        return [param, str(value)]

    def force_value(self, value):
        self._value = json.dumps(value)

    def recreate(self):
        # we want to change filefields to reflect whatever is the current job's path. This is currently used for
        # job resubmission
        value = json.loads(self._value)
        field = self.parameter.form_field
        if field == self.FILE:
            # we are perfectly fine using old input files instead of recreating them, so only check output files
            if self.parameter.is_output:
                new_path = self.job.get_output_path()
                new_root, new_id = os.path.split(new_path)
                # we want to remove the root + the old job's pk
                value = value[value.find(new_root)+len(new_root)+1:]
                value = value[value.find(os.path.sep)+1:]
                # we want to create a new path for the current job
                path = os.path.join(new_path, self.parameter.slug if not value else value)
                value = path
                self._value = json.dumps(value)

    @property
    def value(self):
        value = json.loads(self._value)
        if value is not None:
            field = self.parameter.form_field
            if field == self.FILE:
                try:
                    file_obj = utils.get_storage_object(value)
                    value = file_obj
                except IOError:
                    # this can occur when the storage object is not yet made for output
                    if self.parameter.is_output:
                        return value
                    raise IOError
        return value

    @value.setter
    def value(self, value):
        # coerce the value to the proper type and store as json to make it persistent as well as have json
        #  handle type conversion on the way back out
        field = self.parameter.form_field
        if field == self.CHAR:
            if value is None:
                value = None
            elif field == self.CHAR:
                if not value:
                    value = None
            else:
                value = self.DJANGUI_FIELD_MAP[field](value)
        elif field == self.INTEGER:
            value = self.DJANGUI_FIELD_MAP[field](value) if isinstance(value, int) or str(value).isdigit() else None
        elif field == self.BOOLEAN:
            if value is None or value is False:
                value = None
            if value:
                value = True
        elif field == self.FILE:
            if self.parameter.is_output:
                # make a fake object for it
                path = os.path.join(self.job.get_output_path(), self.parameter.slug if not value else value)
                value = path
            else:
                if value:
                    path = os.path.join(self.job.get_upload_path(), os.path.split(value.name)[1])
                    utils.get_storage(local=False).save(path, value)
                    utils.get_storage(local=True).save(path, value)
                    value = path
        self._value = json.dumps(value)


class DjanguiFile(models.Model):
    filepath = models.FileField()
    job = models.ForeignKey('DjanguiJob')
    filepreview = models.TextField(null=True, blank=True)
    filetype = models.CharField(max_length=255, null=True, blank=True)
    parameter = models.ForeignKey('ScriptParameters', null=True, blank=True)
