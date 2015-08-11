from __future__ import absolute_import, print_function, unicode_literals
__author__ = 'chris'
import os
import errno
import importlib
import json
import six
from io import IOBase

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings
from django.core.files.storage import SuspiciousFileOperation
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils.text import get_valid_filename

from autoslug import AutoSlugField

from celery import states

from .. import settings as wooey_settings
from .. backend import utils

from . mixins import UpdateScriptsMixin, ModelDiffMixin, WooeyPy2Mixin
from .. import django_compat


# TODO: Handle cases where celery is not setup but specified to be used
tasks = importlib.import_module(wooey_settings.WOOEY_CELERY_TASKS)

class ScriptGroup(UpdateScriptsMixin, WooeyPy2Mixin, models.Model):
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

    class Meta:
        app_label = 'wooey'

    def __str__(self):
        return self.group_name

class Script(ModelDiffMixin, WooeyPy2Mixin, models.Model):
    script_name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='script_name', unique=True)
    # we create defaults for the script_group in the clean method of the model. We have to set it to null/blank=True
    # or else we will fail form validation before we hit the model.
    script_group = models.ForeignKey('ScriptGroup', null=True, blank=True)
    script_description = models.TextField(blank=True, null=True)
    script_order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    user_groups = models.ManyToManyField(Group, blank=True)
    script_path = models.FileField() if django_compat.DJANGO_VERSION >= django_compat.DJ17 else models.FileField(upload_to=wooey_settings.WOOEY_SCRIPT_DIR)
    execute_full_path = models.BooleanField(default=True) # use full path for subprocess calls
    save_path = models.CharField(max_length=255, blank=True, null=True,
                                 help_text='By default save to the script name,'
                                           ' this will change the output folder.')
    # when a script updates, increment this to keep old scripts that are cloned working. The downside is we get redundant
    # parameters, but even a huge site may only have a few thousand parameters to query though.
    script_version = models.PositiveSmallIntegerField(default=0)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wooey'

    def __str__(self):
        return self.script_name

    def get_url(self):
        return reverse('wooey:wooey_script', kwargs={'slug': self.slug})

    def get_script_path(self):
        path = self.script_path.path
        return path if self.execute_full_path else os.path.split(path)[1]

    def clean(self):
        if self.script_group is None:
            group = ScriptGroup.objects.filter(group_name=wooey_settings.WOOEY_DEFAULT_SCRIPT_GROUP).order_by('pk').first()
            if not group:
                group, created = ScriptGroup.objects.get_or_create(group_name=wooey_settings.WOOEY_DEFAULT_SCRIPT_GROUP)
            self.script_group = group

    @transaction.atomic
    def save(self, **kwargs):
        if 'script_path' in self.changed_fields:
            self.script_version += 1
        new_script = self.pk is None or 'script_path' in self.changed_fields
        # if uploading from the admin, fix its path
        # we do this to avoid having migrations specific to various users with different WOOEY_SCRIPT_DIR settings
        if new_script or wooey_settings.WOOEY_SCRIPT_DIR not in self.script_path.file.name:
            old_path = self.script_path.file.name
            old_name = os.path.split(old_path)[1]
            new_name = os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, old_name)
            # TODO -- versioning of old scripts
            remote_store = utils.get_storage(local=False)
            if remote_store.exists(new_name):
                remote_store.delete(new_name)
            local_storage = utils.get_storage(local=True)
            if local_storage.exists(new_name):
                local_storage.delete(new_name)
            remote_store.save(new_name, self.script_path.file)

            # save it locally as well, check if it exists because for some setups remote=local
            if not local_storage.exists(new_name):
                local_storage.save(new_name, self.script_path.file)
            self.script_path.save(new_name, self.script_path.file, save=False)
            self.script_path.name = new_name
            if old_name != new_name:
                if local_storage.exists(old_name):
                    local_storage.delete(old_name)
            # clone ourselves if we are updating a script
            self.pk = None
        super(Script, self).save(**kwargs)
        if new_script:
            if getattr(self, '_add_script', True):
                added, error = utils.add_wooey_script(script=self, group=self.script_group)
                if added is False:
                    # TODO: Make a better error
                    raise BaseException(error)
        utils.load_scripts()


class WooeyJob(WooeyPy2Mixin, models.Model):
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

    class Meta:
        app_label = 'wooey'

    def __str__(self):
        return self.job_name

    def get_parameters(self):
        return ScriptParameters.objects.filter(job=self).order_by('pk')

    def submit_to_celery(self, **kwargs):
        if kwargs.get('resubmit'):
            params = self.get_parameters()
            user = kwargs.get('user')
            self.pk = None
            self.user = None if user is None or not user.is_authenticated() else user
            # clear the output channels
            self.celery_id = None
            self.stdout = ''
            self.stderr = ''
            self.save()
            with transaction.atomic():
                for param in params:
                    param.pk = None
                    param.job = self
                    param.recreate()
                    param.save()
        self.status = self.SUBMITTED
        self.save()
        task_kwargs = {'wooey_job': self.pk, 'rerun': kwargs.pop('rerun', False)}
        if wooey_settings.WOOEY_CELERY:
            results = tasks.submit_script.delay(**task_kwargs)
        else:
            results = tasks.submit_script(**task_kwargs)
        return self

    def get_resubmit_url(self):
        return reverse('wooey:wooey_script_clone', kwargs={'slug': self.script.slug, 'job_id': self.pk})

    @property
    def output_path(self):
        return os.path.join(wooey_settings.WOOEY_FILE_DIR, get_valid_filename(self.user.username if self.user is not None else ''),
                            get_valid_filename(self.script.slug if not self.script.save_path else self.script.save_path), str(self.pk))

    def get_output_path(self):
        path = self.output_path
        utils.mkdirs(os.path.join(settings.MEDIA_ROOT, path))
        return path

    def get_upload_path(self):
        path = self.output_path
        utils.mkdirs(os.path.join(settings.MEDIA_ROOT, path))
        return path

    def get_relative_path(self, path):
        # We make the filename relative to the MEDIA_ROOT, this is for filesystems that can change between
        # machines. We also want to omit any leading path separators so we can join the path to whatever
        # MEDIA_ROOT is currently at work instead of giving a path from a root
        return path[path.find(self.get_output_path()):].lstrip(os.path.sep)


class ScriptParameterGroup(UpdateScriptsMixin, WooeyPy2Mixin, models.Model):
    group_name = models.TextField()
    script = models.ForeignKey('Script')

    class Meta:
        app_label = 'wooey'

    def __str__(self):
        return '{}: {}'.format(self.script.script_name, self.group_name)


class ScriptParameter(UpdateScriptsMixin, WooeyPy2Mixin, models.Model):
    """
        This holds the parameter mapping for each script, and enforces uniqueness by each script via a FK.
    """
    script = models.ForeignKey('Script')
    short_param = models.CharField(max_length=255)
    script_param = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='script_param', unique=True)
    is_output = models.BooleanField(default=None)
    required = models.BooleanField(default=False)
    # output_path = models.FilePathField(path=settings.MEDIA_ROOT, allow_folders=True, allow_files=False,
    #                                    recursive=True, max_length=255)
    choices = models.CharField(max_length=255, null=True, blank=True)
    choice_limit = models.CharField(max_length=10, null=True, blank=True)
    form_field = models.CharField(max_length=255)
    default = models.CharField(max_length=255, null=True, blank=True)
    input_type = models.CharField(max_length=255)
    param_help = models.TextField(verbose_name='help', null=True, blank=True)
    is_checked = models.BooleanField(default=False)
    parameter_group = models.ForeignKey('ScriptParameterGroup')

    class Meta:
        app_label = 'wooey'

    @property
    def multiple_choice(self):
        choice_limit = json.loads(self.choice_limit)
        if choice_limit is None:
            return False
        try:
            choice_limit = int(choice_limit)
        except ValueError:
            # it's not a set # of choices that is a max, it's either >=0, or >=1, which are the same for a front-end
            # since validation of >=0 or >=1 is performed outside of the form.
            return True
        else:
            return choice_limit > 1

    @property
    def max_choices(self):
        choice_limit = json.loads(self.choice_limit)
        if choice_limit is None:
            return 1
        try:
            choice_limit = int(choice_limit)
        except ValueError:
            # for this, it's either >=0 or >=1 so as many as they want.
            return -1
        else:
            return choice_limit

    def __str__(self):
        return '{}: {}'.format(self.script.script_name, self.script_param)


# TODO: find a better name for this class
class ScriptParameters(WooeyPy2Mixin, models.Model):
    """
        This holds the actual parameters sent with the submission
    """
    # the details of the actual executed scripts
    job = models.ForeignKey('WooeyJob')
    parameter = models.ForeignKey('ScriptParameter')
    # we store a JSON dumped string in here to attempt to keep our types in order
    _value = models.TextField(db_column='value')

    BOOLEAN = 'BooleanField'
    CHAR = 'CharField'
    CHOICE = 'ChoiceField'
    FILE = 'FileField'
    FLOAT = 'FloatField'
    INTEGER = 'IntegerField'

    WOOEY_FIELD_MAP = {
        BOOLEAN: lambda x: str(x).lower() == 'true',
        CHAR: str,
        CHOICE: str,
        FLOAT: float,
        INTEGER: int,
    }

    class Meta:
        app_label = 'wooey'

    def __str__(self):
        try:
            value = self.value
        except IOError:
            value = _('FILE NOT FOUND')
        except SuspiciousFileOperation:
            value = _('File outside of project')
        return '{}: {}'.format(self.parameter.script_param, value)

    def get_subprocess_value(self):
        value = self.value
        if self.value is None:
            return None
        field = self.parameter.form_field
        param = self.parameter.short_param
        com = {'parameter': param}
        if field == self.BOOLEAN:
            if value:
                return com
        if field == self.FILE:
            if self.parameter.is_output:
                try:
                    value = value.path
                except AttributeError:
                    value = utils.get_storage(local=True).path(value)
                    # trim the output path, we don't want to be adding our platform specific paths to the output
                    op = self.job.get_output_path()
                    #TODO : use os.path.sep
                    value = value[value.find(op)+len(op)+1:]
            else:
                # make sure we have it locally otherwise download it
                if not utils.get_storage(local=True).exists(value.path):
                    new_path = utils.get_storage(local=True).save(value.path, value)
                    value = new_path
                else:
                    # return the string for processing
                    value = value.path
        try:
            float(value)
            value = str(value)
        except ValueError:
            pass
        com['value'] = value if isinstance(value, six.string_types) else six.u(value)
        return com

    def force_value(self, value):
        self._value = json.dumps(value)

    def recreate(self):
        # we want to change filefields to reflect whatever is the current job's path. This is currently used for
        # job resubmission
        value = json.loads(self._value)
        if value is not None:
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
        add_file = False
        if field == self.CHAR:
            if value is None:
                value = None
            elif field == self.CHAR:
                if not value:
                    value = None
            else:
                value = self.WOOEY_FIELD_MAP[field](value)
        elif field == self.INTEGER:
            value = self.WOOEY_FIELD_MAP[field](value) if isinstance(value, int) or str(value).isdigit() else None
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
                    local_storage = utils.get_storage(local=True)
                    if hasattr(value, 'size'):
                        filesize = value.size
                    elif issubclass(type(value), IOBase):
                        value.seek(0,2)
                        filesize = value.tell()
                        value.seek(0)
                    else:
                        filesize = None
                    if not local_storage.exists(path) or (filesize is not None and local_storage.size(path) != filesize):
                        local_path = local_storage.save(path, value)
                    else:
                        local_path = local_storage.path(path)
                    remote_storage = utils.get_storage(local=False)
                    if not remote_storage.exists(path) or (filesize is not None and remote_storage.size(path) != filesize):
                        remote_storage.save(local_path, value)
                    add_file = True
                    value = local_path
        self._value = json.dumps(value)
        if add_file:
            # make a WooeyFile so the user can share it/etc.
            # get the system path for the file
            local_path = utils.get_storage(local=True).path(local_path)
            fileinfo = utils.get_file_info(local_path)
            # save ourself first, we have to do this because we are referenced in WooeyFile
            self.save()
            dj_file = WooeyFile(job=self.job, filetype=fileinfo.get('type'),
                                  filepreview=fileinfo.get('preview'), parameter=self)
            save_file = utils.get_storage().open(local_path)
            save_path = self.job.get_relative_path(local_path)
            dj_file.filepath.save(save_path, save_file, save=False)
            dj_file.filepath.name = save_path
            dj_file.save()


class WooeyFile(WooeyPy2Mixin, models.Model):
    filepath = models.FileField(max_length=500) if django_compat.DJANGO_VERSION >= django_compat.DJ17 else models.FileField(max_length=500, upload_to=wooey_settings.WOOEY_SCRIPT_DIR)
    job = models.ForeignKey('WooeyJob')
    filepreview = models.TextField(null=True, blank=True)
    filetype = models.CharField(max_length=255, null=True, blank=True)
    size_bytes = models.IntegerField(null=True)
    parameter = models.ForeignKey('ScriptParameters', null=True, blank=True)

    class Meta:
        app_label = 'wooey'

    def __str__(self):
        return '{}: {}'.format(self.job.job_name, self.filepath)
