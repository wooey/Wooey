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
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from autoslug import AutoSlugField

from ..backend import utils


# TODO: Handle cases where celery is not used
tasks = importlib.import_module(getattr(settings, 'DJANGUI_CELERY_TASKS', 'djangui.tasks'))

# TODO: Add user rights, hide/lock/ordering in an inherited class to cover scriptgroup/scripts

class ScriptGroup(models.Model):
    """
        This is a group of scripts, it holds general information
        about a collection of scripts, and allows for custom descriptions

    """
    group_name = models.TextField()
    group_description = models.TextField(null=True, blank=True)
    slug = AutoSlugField(populate_from='group_name')

class Script(models.Model):
    # blank=True, null=True is to allow anonymous users to submit jobs
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    script_name = models.CharField(max_length=255)

    slug = AutoSlugField(populate_from='script_name')
    script_group = models.ForeignKey('ScriptGroup')
    script_description = models.TextField(blank=True, null=True)
    script_order = models.PositiveSmallIntegerField(default=1)
    script_active = models.BooleanField(default=True)
    script_path = models.CharField(max_length=255)#, default="/home/chris/Devel/djangui/djangui/tests/scripts/fetch_cats.py")
    execute_full_path = models.BooleanField(default=True) # use full path for subprocess calls
    save_path = models.CharField(max_length=255, blank=True, null=True)
    # when a script updates, increment this to keep old scripts that are cloned working. The downside is we get redundant
    # parameters, but even a huge site may only have a few thousand parameters to query though.
    script_version = models.PositiveSmallIntegerField(default=0)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def get_url(self):
        return reverse('djangui_script', kwargs={'script_group': self.script_group.slug,
                                                      'script_name': self.slug})

    def get_script_path(self):
        return self.script_path if self.execute_full_path else os.path.split(self.script_path)[1]


class DjanguiJob(models.Model):
    """
    This model serves to link the submitted celery tasks to a script submitted
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    celery_id = models.CharField(max_length=255, null=True)
    job_name = models.CharField(max_length=255)
    job_description = models.TextField(null=True, blank=True)
    celery_state = models.CharField(max_length=255, blank=True, null=True)
    save_path = models.CharField(max_length=255, blank=True, null=True)
    command = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    script = models.ForeignKey('Script')

    def get_parameters(self):
        return ScriptParameters.objects.filter(job=self)

    def submit_to_celery(self, command=None, resubmit=False):
        if command is None:
            command = utils.get_script_commands(script=self.script, parameters=ScriptParameters.objects.filter(job=self))
        if resubmit:
            # clone ourselves
            self.pk = None
        folder = str(DjanguiJob.objects.count())
        cwd = os.path.join(settings.MEDIA_ROOT, self.user.username if self.user is not None else '', folder)
        abscwd = os.path.abspath(cwd)
        try:
            os.makedirs(abscwd)
        except OSError as exc:
            # directory already exists
            if exc.errno == errno.EEXIST and os.path.isdir(abscwd):
                pass
            else:
                raise
        self.command = ' '.join(command)
        self.save_path = folder
        if getattr(settings, 'DJANGUI_CELERY', False):
            results = tasks.submit_script.delay(command, djangui_cwd=abscwd)
            self.celery_id = results.id
            self.celery_state = results.state
        else:
            results = tasks.submit_script(command, djangui_cwd=abscwd)
        self.save()

    def get_resubmit_url(self):
        return reverse('djangui_script_clone', kwargs={'script_group': self.script.script_group.slug,
                                                      'script_name': self.script.slug, 'task_id': self.celery_id})

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
        path = os.path.join(self.user.username if self.user is not None else '', self.script.slug, str(DjanguiJob.objects.count()))
        self.mkdirs(path)
        return path

    def get_upload_path(self):
        path = os.path.join(self.user.username if self.user is not None else '', self.script.slug)#os.path.join(settings.MEDIA_ROOT, self.slug)
        self.mkdirs(path)
        return path


class AddScript(models.Model):
    """
        This model serves to allow users to upload scripts through the admin. It's a bit redundant, but it's a simple
        integration with the admin.
    """
    script_name = models.CharField(max_length=255, null=True, blank=True)
    script_path = models.FileField(help_text=_('The file to Djanguify'), upload_to='djangui_scripts')
    script_group = models.ForeignKey('ScriptGroup')

    @transaction.atomic
    def save(self, **kwargs):
        super(AddScript, self).save(**kwargs)
        utils.add_djangui_script(script=self.script_path.path, group=self.script_group.group_name, display_name=self.script_name)


class ScriptParameterGroup(models.Model):
    group_name = models.TextField()
    script = models.ForeignKey('Script')


class ScriptParameter(models.Model):
    """
        This holds the parameter mapping for each script, and enforces uniqueness by each script via a FK.
    """
    script = models.ForeignKey('Script')
    short_param = models.CharField(max_length=255)
    script_param = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='script_param')
    is_output = models.BooleanField(default=None)
    required = models.BooleanField(default=False)
    output_path = models.FilePathField(path=settings.MEDIA_ROOT, allow_folders=True, allow_files=False,
                                       recursive=True, max_length=255)
    choices = models.CharField(max_length=255, null=True, blank=True)
    choice_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    form_field = models.CharField(max_length=255)
    default = models.CharField(max_length=255, null=True, blank=True)
    input_type = models.CharField(max_length=255)
    param_help = models.TextField(verbose_name='help')
    is_checked = models.BooleanField(default=False)
    parameter_group = models.ForeignKey('ScriptParameterGroup')


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
            # import ipdb; ipdb.set_trace();
            value = value.name
        return [param, str(value)]

    @property
    def value(self):
        value = json.loads(self._value)
        if value is not None:
            field = self.parameter.form_field
            if field == self.FILE:
                file_obj = utils.get_storage_object(value)
                value = file_obj
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
            _file = None
            if self.parameter.is_output:
                # make a fake object for it
                path = os.path.join(self.parameter.script.get_output_path(), self.parameter.slug)
                _file = ContentFile('')
            else:
                if value:
                    _file = value
                    path = os.path.join(self.parameter.script.get_upload_path(), value.name)
            if _file is not None:
                default_storage.save(path, _file)
                value = path
            else:
                value = None
        self._value = json.dumps(value)