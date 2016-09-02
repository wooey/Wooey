from __future__ import absolute_import, print_function, unicode_literals
__author__ = 'chris'
import os
import errno
import importlib
import json
import six
import uuid
from io import IOBase

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings
from django.core.files.storage import SuspiciousFileOperation
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.utils.text import get_valid_filename

from autoslug import AutoSlugField

from celery import states

from .. import settings as wooey_settings
from .. backend import utils
from ..django_compat import get_cache

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
        verbose_name = _('script group')
        verbose_name_plural = _('script groups')

    def __str__(self):
        return self.group_name


class Script(ModelDiffMixin, WooeyPy2Mixin, models.Model):
    script_name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='script_name', unique=True)
    # we create defaults for the script_group in the clean method of the model. We have to set it to null/blank=True
    # or else we will fail form validation before we hit the model.
    script_group = models.ForeignKey('ScriptGroup', null=True, blank=True)
    script_description = models.TextField(blank=True, null=True)
    documentation = models.TextField(blank=True, null=True)
    script_order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    user_groups = models.ManyToManyField(Group, blank=True)

    execute_full_path = models.BooleanField(default=True)  # use full path for subprocess calls
    save_path = models.CharField(max_length=255, blank=True, null=True,
                                 help_text='By default save to the script name,'
                                           ' this will change the output folder.')

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wooey'
        verbose_name = _('script')
        verbose_name_plural = _('scripts')

    def __str__(self):
        return self.script_name

    def get_url(self):
        return reverse('wooey:wooey_script', kwargs={'slug': self.slug})

    @property
    def latest_version(self):
        return self.script_version.get(default_version=True)

    def clean(self):
        if self.script_group is None:
            group = ScriptGroup.objects.filter(group_name=wooey_settings.WOOEY_DEFAULT_SCRIPT_GROUP).order_by('pk').first()
            if not group:
                group, created = ScriptGroup.objects.get_or_create(group_name=wooey_settings.WOOEY_DEFAULT_SCRIPT_GROUP)
            self.script_group = group

    def get_previous_versions(self):
        return self.script_version.all().order_by('script_version', 'script_iteration')


class ScriptVersion(ModelDiffMixin, WooeyPy2Mixin, models.Model):
    # when a script updates, increment this to keep old scripts that are cloned working. The downside is we get redundant
    # parameters, but even a huge site may only have a few thousand parameters to query though.
    script_version = models.CharField(max_length=50, help_text='The script version.', blank=True, default='1')
    script_iteration = models.PositiveSmallIntegerField(default=1)
    script_path = models.FileField() if django_compat.DJANGO_VERSION >= django_compat.DJ17 else models.FileField(upload_to=wooey_settings.WOOEY_SCRIPT_DIR)
    default_version = models.BooleanField(default=False)
    script = models.ForeignKey('Script', related_name='script_version')

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wooey'
        verbose_name = _('script version')
        verbose_name_plural = _('script versions')

    def __str__(self):
        return '{}({}: {})'.format(self.script.script_name, self.script_version, self.script_iteration)

    def get_url(self):
        return reverse('wooey:wooey_script', kwargs={'slug': self.script.slug})

    def get_script_path(self):
        local_storage = utils.get_storage(local=True)
        path = local_storage.path(self.script_path.path)
        return path if self.script.execute_full_path else os.path.split(path)[1]

    def get_parameters(self):
        return ScriptParameter.objects.filter(script_version=self).order_by('param_order', 'pk')


class WooeyJob(WooeyPy2Mixin, models.Model):
    """
    This model serves to link the submitted celery tasks to a script submitted
    """
    # blank=True, null=True is to allow anonymous users to submit jobs
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    celery_id = models.CharField(max_length=255, null=True)
    uuid = models.CharField(max_length=255, default=uuid.uuid4, unique=True)
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
    script_version = models.ForeignKey('ScriptVersion')

    class Meta:
        app_label = 'wooey'
        verbose_name = _('wooey job')
        verbose_name_plural = _('wooey jobs')

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
            self.uuid = uuid.uuid4()
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

        if task_kwargs.get('rerun'):
            utils.purge_output(job=self)
        if wooey_settings.WOOEY_CELERY:
            results = tasks.submit_script.delay(**task_kwargs)
        else:
            results = tasks.submit_script(**task_kwargs)
        return self

    def get_resubmit_url(self):
        return reverse('wooey:wooey_script_clone', kwargs={'slug': self.script_version.script.slug, 'job_id': self.pk})

    @property
    def output_path(self):
        return os.path.join(wooey_settings.WOOEY_FILE_DIR,
                            get_valid_filename(self.user.username if self.user is not None else ''),
                            get_valid_filename(self.script_version.script.slug if not self.script_version.script.save_path else self.script_version.script.save_path),
                            str(self.uuid))

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

    def get_realtime_key(self):
        return 'wooeyjob_{}_rt'.format(self.pk)

    def update_realtime(self, stdout='', stderr='', delete=False):
        wooey_cache = wooey_settings.WOOEY_REALTIME_CACHE
        if delete == False and wooey_cache is None:
            self.stdout = stdout
            self.stderr = stderr
            self.save()
        elif wooey_cache is not None:
            cache = get_cache(wooey_cache)
            if delete:
                cache.delete(self.get_realtime_key())
            else:
                cache.set(self.get_realtime_key(), json.dumps({'stdout': stdout, 'stderr': stderr}))

    def get_realtime(self):
        wooey_cache = wooey_settings.WOOEY_REALTIME_CACHE
        if wooey_cache is not None:
            cache = get_cache(wooey_cache)
            out = cache.get(self.get_realtime_key())
            if out:
                return json.loads(out)
        return {'stdout': self.stdout, 'stderr': self.stderr}

    def get_stdout(self):
        if self.status != WooeyJob.COMPLETED:
            rt = self.get_realtime().get('stdout')
            if rt:
                return rt
        return self.stdout

    def get_stderr(self):
        if self.status != WooeyJob.COMPLETED:
            rt = self.get_realtime().get('stderr')
            if rt:
                return rt
        return self.stderr


class ScriptParameterGroup(UpdateScriptsMixin, WooeyPy2Mixin, models.Model):
    group_name = models.TextField()
    hidden = models.BooleanField(default=False)
    script_version = models.ForeignKey('ScriptVersion')

    class Meta:
        app_label = 'wooey'
        verbose_name = _('script parameter group')
        verbose_name_plural = _('script parameter groups')

    def __str__(self):
        return '{}: {}'.format(self.script_version.script.script_name, self.group_name)


class ScriptParameter(UpdateScriptsMixin, WooeyPy2Mixin, models.Model):
    """
        This holds the parameter mapping for each script, and enforces uniqueness by each script via a FK.
    """
    script_version = models.ManyToManyField('ScriptVersion')
    short_param = models.CharField(max_length=255, blank=True)
    script_param = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='script_param', unique=True)
    is_output = models.BooleanField(default=None)
    required = models.BooleanField(default=False)
    choices = models.CharField(max_length=255, null=True, blank=True)
    choice_limit = models.CharField(max_length=10, null=True, blank=True)
    collapse_arguments = models.BooleanField(
        default=True,
        help_text=_('Collapse separate inputs to a given argument to a single input (ie: --arg 1 --arg 2 becomes --arg 1 2)')
    )
    form_field = models.CharField(max_length=255)
    default = models.CharField(max_length=255, null=True, blank=True)
    input_type = models.CharField(max_length=255)
    param_help = models.TextField(verbose_name='help', null=True, blank=True)
    is_checked = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    parameter_group = models.ForeignKey('ScriptParameterGroup')
    param_order = models.SmallIntegerField('The order the parameter appears to the user.', default=0)

    class Meta:
        app_label = 'wooey'
        verbose_name = _('script parameter')
        verbose_name_plural = _('script parameters')

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
        scripts = ', '.join([i.script.script_name for i in self.script_version.all()])
        return '{}: {}'.format(scripts, self.script_param)


# TODO: find a better name for this class. Job parameter? SelectedParameter?
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
        verbose_name = _('script parameters')

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
        com = {'parameter': param, 'script_parameter': self.parameter}
        if field == self.BOOLEAN:
            if value:
                return com
            else:
                del com['parameter']
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
        checksum = None
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
            if value is None or value == False:
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
                    local_storage = utils.get_storage(local=True)
                    current_path = local_storage.path(value)
                    checksum = utils.get_checksum(value)
                    path = utils.get_upload_path(current_path, checksum=checksum)
                    if hasattr(value, 'size'):
                        filesize = value.size
                    elif issubclass(type(value), IOBase):
                        value.seek(0, 2)
                        filesize = value.tell()
                        value.seek(0)
                    else:
                        filesize = None
                    if not local_storage.exists(path) or (filesize is not None and local_storage.size(path) != filesize):
                        local_path = local_storage.save(path, value)
                    else:
                        local_path = local_storage.path(path)
                        local_path = os.path.join(os.path.split(path)[0], os.path.split(local_path)[1])
                    remote_storage = utils.get_storage(local=False)
                    if not remote_storage.exists(path) or (filesize is not None and remote_storage.size(path) != filesize):
                        local_path = remote_storage.save(local_path, value)
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
            if checksum is None:
                checksum = utils.get_checksum(local_path)
            wooey_file, file_created = WooeyFile.objects.get_or_create(checksum=checksum)
            if file_created:
                wooey_file.filetype = fileinfo.get('type')
                wooey_file.filepreview = fileinfo.get('preview')
                save_file = utils.get_storage().open(local_path)
                save_path = path
                wooey_file.filepath.save(save_path, save_file, save=False)
                wooey_file.filepath.name = save_path
                wooey_file.save()

            UserFile.objects.get_or_create(job=self.job, system_file=wooey_file,
                                           parameter=self, filename=os.path.split(local_path)[1])


class UserFile(WooeyPy2Mixin, models.Model):
    filename = models.TextField()
    job = models.ForeignKey('WooeyJob')
    system_file = models.ForeignKey('WooeyFile')
    parameter = models.ForeignKey('ScriptParameters', null=True, blank=True)

    class Meta:
        app_label = 'wooey'

    def __str__(self):
        return '{}: {}'.format(self.job.job_name, self.system_file)


class WooeyFile(WooeyPy2Mixin, models.Model):
    filepath = models.FileField(max_length=500) if django_compat.DJANGO_VERSION >= django_compat.DJ17 else models.FileField(max_length=500, upload_to=wooey_settings.WOOEY_SCRIPT_DIR)
    filepreview = models.TextField(null=True, blank=True)
    filetype = models.CharField(max_length=255, null=True, blank=True)
    size_bytes = models.IntegerField(null=True)
    checksum = models.CharField(max_length=40, blank=True)

    class Meta:
        app_label = 'wooey'
        verbose_name = _('wooey file')
        verbose_name_plural = _('wooey files')

    def __str__(self):
        return self.filepath.name
