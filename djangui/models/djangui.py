__author__ = 'chris'
import os
import errno
import importlib
import json
import subprocess
import imp
import sys
from itertools import chain
import traceback
import tempfile
from argparse import ArgumentParser, FileType

from django.template import Context, Engine
from django.db import models
from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.forms import fields

from autoslug import AutoSlugField


from ..backend.argparse_specs import ArgParseNodeBuilder
from ..backend import utils
from ..backend.ast import source_parser


# TODO: Handle cases where celery is not used
tasks = importlib.import_module(settings.DJANGUI_CELERY_TASKS)

class ScriptBase(models.Model):
    # blank=True, null=True is to allow anonymous users to submit jobs
    # TODO: add a setting for allowing anonymous users
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    job_name = models.CharField(max_length=255)
    job_description = models.TextField(null=True, blank=True)
    command = models.TextField(null=True, blank=True)
    celery_id = models.CharField(max_length=255, blank=True, null=True)
    celery_state = models.CharField(max_length=255, blank=True, null=True)
    save_path = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DjanguiJob(models.Model):
    """
    This model serves to link the submitted celery tasks to a script submitted
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    celery_id = models.CharField(max_length=255, null=True)
    job_name = models.CharField(max_length=255)
    job_description = models.TextField(null=True, blank=True)
    script_command = models.TextField(null=True, blank=True)
    celery_state = models.CharField(max_length=255, blank=True, null=True)
    save_path = models.CharField(max_length=255, blank=True, null=True)
    command = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    script = models.ForeignKey('Script')

    def get_parameters(self):
        return ScriptParameters.objects.filter(job=self)

    def submit_to_celery(self, command=None, resubmit=False):
        # import ipdb; ipdb.set_trace();
        if command is None:
            command = utils.get_script_commands(ScriptParameters.objects.filter(job=self))
        if resubmit:
            # clone ourselves
            self.pk = None
        folder = str(DjanguiJob.objects.count())
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
        results = tasks.submit_script.delay(command, djangui_cwd=abscwd)
        self.command = ' '
        self.save_path = folder
        self.celery_id = results.id
        self.celery_state = results.state
        self.save()

    def get_resubmit_url(self):
        return reverse('djangui_script_clone', kwargs={'script_group': self.script.script_group.slug,
                                                      'script_name': self.script.slug, 'task_id': self.celery_id})


class ScriptGroup(models.Model):
    """
        This is a group of scripts, it is essentially the base app the holds general information
        about the script group
    """
    group_name = models.TextField()
    group_description = models.TextField(null=True, blank=True)
    slug = AutoSlugField(populate_from='group_name')


class AddScript(models.Model):
    """
        This tracks scripts upload, it's useful to keep it as a model so the user can easily check for updates
    """
    script_path = models.FileField(help_text=_('The file to Djanguify'))
    script_group = models.ForeignKey('ScriptGroup')

    @transaction.atomic
    def save(self, **kwargs):
        super(AddScript, self).save(**kwargs)
        script = self.script_path.path
        basename, extension = os.path.splitext(script)
        filename = os.path.split(basename)[1]

        parser = ArgParseNodeBuilder(script_name=filename, script_path=script)
        # make our script
        d = parser.get_script_description()
        djangui_script, created = Script.objects.get_or_create(script_group=self.script_group, script_description=d['description'],
                                       script_path=script, script_name=d['name'])
        if not created:
            djangui_script.script_version += 1
            djangui_script.save()
        # make our parameters
        CHOICE_MAPPING = {

        }
        for param_group_info in d['inputs']:
            param_group, created = ScriptParameterGroup.objects.get_or_create(group_name=param_group_info.get('group'), script=djangui_script)
            for param in param_group_info.get('nodes'):
                # TODO: fix choice limits
                #choice_limit = CHOICE_MAPPING[param.get('choice_limit')]
                # TODO: fix 'file' to be global in argparse
                is_out = True if param.get('upload', None) is False and param.get('type') == 'file' else not param.get('upload', False)
                print param, is_out
                script_param, created = ScriptParameter.objects.get_or_create(script=djangui_script, short_param=param['param'], script_param=param['name'],
                                                      is_output=is_out, required=param.get('required', False),
                                                      form_field=param['model'], default=param.get('default'), input_type=param.get('type'),
                                                      choices=json.dumps(param.get('choices')), choice_limit=None,
                                                      param_help=param.get('help'), is_checked=param.get('checked', False),
                                                      parameter_group=param_group)
        # upload our loaded scripts
        utils.load_scripts()



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


class ScriptParameters(models.Model):
    # the details of the actual executed scripts
    job = models.ForeignKey('DjanguiJob')
    parameter = models.ForeignKey('ScriptParameter')
    # subprocess only takes strings, so we don't need to worry about type coercion & tracking
    # the Nonetype is reserved for when a field parameter is to be omitted
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
                # import ipdb; ipdb.set_trace();
                file_obj = default_storage.open(value)
                file_obj.url = default_storage.url(value)
                file_obj.path = default_storage.path(value)
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
                path = os.path.join(self.parameter.script.get_upload_path(), self.parameter.slug)
                _file = ContentFile('')
            else:
                if value:
                    _file = value
                    path = os.path.join(self.parameter.script.get_output_path(), value.name)
            if _file is not None:
                default_storage.save(path, _file)
                value = path
            else:
                value = None
        self._value = json.dumps(value)


class Script(ScriptBase):
    script_name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='script_name')
    script_group = models.ForeignKey('ScriptGroup')
    script_description = models.TextField(blank=True, null=True)
    script_order = models.PositiveSmallIntegerField(default=1)
    script_active = models.BooleanField(default=True)
    script_path = models.CharField(max_length=255)#, default="/home/chris/Devel/djangui/djangui/tests/scripts/fetch_cats.py")
    execute_full_path = models.BooleanField(default=True) # use full path for subprocess calls
    # when a script updates, increment this to keep old scripts that are cloned working. The downside is we get redundant
    # parameters, but even a huge site may only have a few thousand parameters to query though.
    script_version = models.PositiveSmallIntegerField(default=0)

    def get_url(self):
        return reverse('djangui_script', kwargs={'script_group': self.script_group.slug,
                                                      'script_name': self.slug})

    def get_script_path(self):
        return self.script_path if self.execute_full_path else os.path.split(self.script_path)[1]

    def get_output_path(self):
        path = os.path.join(self.slug, str(DjanguiJob.objects.count()))
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
        return path

    def get_upload_path(self):
        path = self.slug#os.path.join(settings.MEDIA_ROOT, self.slug)
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
        return path