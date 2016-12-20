from __future__ import absolute_import
__author__ = 'chris'
import json
import errno
import os
import re
import sys
import six
import uuid
import traceback
from operator import itemgetter
from collections import OrderedDict, defaultdict
from pkg_resources import parse_version

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.utils import OperationalError
from django.core.files.storage import default_storage
from django.core.files import File
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from celery.contrib import rdb
# Python2.7 encoding= support
from io import open

from clinto.parser import Parser

from .. import settings as wooey_settings


def sanitize_name(name):
    return name.replace(' ', '_').replace('-', '_')


def sanitize_string(value):
    return value.replace('"', '\\"')


def get_storage(local=True):
    if wooey_settings.WOOEY_EPHEMERAL_FILES:
        storage = default_storage.local_storage if local else default_storage
    else:
        storage = default_storage
    return storage


def purge_output(job=None):
    from ..models import UserFile
    # cleanup the old files, we need to be somewhat aggressive here.
    local_storage = get_storage(local=True)
    for user_file in UserFile.objects.filter(job=job):
        if user_file.parameter is None or user_file.parameter.parameter.is_output:
            system_file = user_file.system_file
            matching_files = UserFile.objects.filter(system_file=system_file).exclude(job=user_file.job)
            # nothing else references this file, delete it
            if matching_files.count() == 0:
                wooey_file = system_file.filepath.name
                # this will delete the default file -- which if we are using an ephemeral file system will be the
                # remote instance
                system_file.filepath.delete(False)
                system_file.delete()
                # check our local storage and remove it if it is there as well
                path = local_storage.path(wooey_file)
                if local_storage.exists(path):
                    local_storage.delete(path)
            # delete all copies this user has of this file.
            user_file.delete()


def get_job_commands(job=None):
    script_version = job.script_version
    com = [sys.executable] if sys.executable else []
    com.extend([script_version.get_script_path()])
    parameters = job.get_parameters()
    param_dict = OrderedDict()
    param_info_dict = {}
    for param in parameters:
        subproc_dict = param.get_subprocess_value()
        if subproc_dict is None:
            continue
        subproc_param = subproc_dict['parameter']
        param_info_dict[subproc_param] = subproc_dict['script_parameter']
        if subproc_param not in param_dict:
            param_dict[subproc_param] = []
        subproc_value = subproc_dict.get('value', None)
        if subproc_value:
            param_dict[subproc_param].append(subproc_value)
    for param, values in param_dict.items():
        param_info = param_info_dict.get(param, None)
        if param and not values:
            com.append(param)
        else:
            for index, value in enumerate(values):
                if param and (param_info is None or param_info.collapse_arguments == False or index == 0):
                    com.append(param)
                com.append(value)
    return com


@transaction.atomic
def create_wooey_job(user=None, script_version_pk=None, data=None):
    from ..models import Script, WooeyJob, ScriptParameter, ScriptParameters, ScriptVersion
    script_version = ScriptVersion.objects.select_related('script').get(pk=script_version_pk)
    if data is None:
        data = {}
    job = WooeyJob(user=user, job_name=data.pop('job_name', None), job_description=data.pop('job_description', None),
                     script_version=script_version)
    job.save()
    # Because we use slugs, we do not need to filter by script_version=script_version here. We are going to eventually
    # have a setup where Script points at ScriptParameter instead of SP->SV. This will let us reuse slugs for
    # a script class
    parameters = OrderedDict([(i.slug, i) for i in ScriptParameter.objects.filter(slug__in=data.keys()).order_by('param_order', 'pk')])
    for slug, param in six.iteritems(parameters):
        slug_values = data.get(slug)
        slug_values = slug_values if isinstance(slug_values, list) else [slug_values]
        for slug_value in slug_values:
            new_param = ScriptParameters(job=job, parameter=param)
            new_param.value = slug_value
            new_param.save()
    return job


def get_master_form(script_version=None, pk=None):
    from ..forms.factory import DJ_FORM_FACTORY
    return DJ_FORM_FACTORY.get_master_form(script_version=script_version, pk=pk)


def get_form_groups(script_version=None, pk=None, initial_dict=None, render_fn=None):
    from ..forms.factory import DJ_FORM_FACTORY
    return DJ_FORM_FACTORY.get_group_forms(script_version=script_version, pk=pk, initial_dict=initial_dict, render_fn=render_fn)


def reset_form_factory(script_version=None):
    from ..forms.factory import DJ_FORM_FACTORY
    DJ_FORM_FACTORY.reset_forms(script_version=script_version)


def validate_form(form=None, data=None, files=None):
    form.add_wooey_fields()
    form.data = data if data is not None else {}
    form.files = files if files is not None else {}
    form.is_bound = True
    form.full_clean()


def get_current_scripts():
    from ..models import ScriptVersion
    try:
        scripts = ScriptVersion.objects.count()
    except OperationalError:
        # database not initialized yet
        return

    # get the scripts with default version
    scripts = ScriptVersion.objects.select_related('script').filter(default_version=True)
    # scripts we need to figure out the default version for some reason
    non_default_scripts = ScriptVersion.objects.filter(default_version=False).exclude(script__in=[i.script for i in scripts])
    script_versions = defaultdict(list)
    for sv in non_default_scripts:
        try:
            version_string = parse_version(str(sv.script_version))
        except:
            sys.stderr.write('Error converting script version:\n{}'.format(traceback.format_exc()))
            version_string = sv.script_version
        script_versions[sv.script.script_name].append((version_string, sv.script_iteration, sv))
        [script_versions[i].sort(key=itemgetter(0, 1, 2), reverse=True) for i in script_versions]
    scripts = [i.script for i in scripts]
    if script_versions:
        for script_version_info in script_versions.values():
            new_scripts = ScriptVersion.objects.select_related('script').filter(pk__in=[i[2].pk for i in script_version_info])
            scripts.extend([i.script for i in new_scripts])
    return scripts


def get_storage_object(path, local=False):
    storage = get_storage(local=local)
    obj = storage.open(path)
    obj.url = storage.url(path)
    obj.path = storage.path(path)
    return obj


def add_wooey_script(script_version=None, script_path=None, group=None, script_name=None):
    # There is a class called 'Script' which contains the general information about a script. However, that is not where the file details
    # of the script lie. That is the ScriptVersion model. This allows the end user to tag a script as a favorite/etc. and set
    # information such as script descriptions/names that do not constantly need to be updated with every version change. Thus,
    # a ScriptVersion stores the file info and such.
    from ..models import Script, ScriptGroup, ScriptParameter, ScriptParameterGroup, ScriptVersion
    # if we are adding through the admin, at this point the file will be saved already and this method will be receiving
    # the scriptversion object. Otherwise, we are adding through the managementment command. In this case, the file will be
    # a location and we need to setup the Script and ScriptVersion in here.

    local_storage = get_storage(local=True)
    if script_version is not None:
        # we are updating the script here or creating it through the admin

        # we need to move the script to the wooey scripts directory now
        # handle remotely first, because by default scripts will be saved remotely if we are using an
        # ephemeral file system
        old_name = script_version.script_path.name
        new_name = os.path.normpath(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, old_name) if not old_name.startswith(wooey_settings.WOOEY_SCRIPT_DIR) else old_name)

        current_storage = get_storage(local=not wooey_settings.WOOEY_EPHEMERAL_FILES)
        current_file = current_storage.open(old_name)
        if current_storage.exists(new_name):
            new_name = current_storage.get_available_name(new_name)
        new_path = current_storage.save(new_name, current_file)

        # remove the old file
        if old_name != new_name:
            current_file.close()
            current_storage.delete(old_name)
            current_file = current_storage.open(new_path)

        script_version._rename_script = True
        script_version.script_path.name = new_name
        script_version.save()

        # download the script locally if it doesn't exist
        if not local_storage.exists(new_path):
            new_path = local_storage.save(new_path, current_file)

        script = get_storage_object(new_path, local=True).path
        local_file = local_storage.open(new_path).name
    else:
        # we got a path, if we are using a remote file system, it will be located remotely by default
        # make sure we have it locally as well
        if wooey_settings.WOOEY_EPHEMERAL_FILES:
            remote_storage = get_storage(local=False)
            remote_file = remote_storage.open(script_path)
            local_file = local_storage.save(script_path, remote_file)
        else:
            local_file = local_storage.open(script_path).name
        script = get_storage_object(local_file, local=True).path

    if isinstance(group, ScriptGroup):
        group = group.group_name
    if group is None:
        group = 'Wooey Scripts'
    basename, extension = os.path.splitext(script)
    filename = os.path.split(basename)[1]

    parser = Parser(script_name=filename, script_path=local_storage.path(local_file))
    if not parser.valid:
        return {'valid': False, 'errors': parser.error}
    # make our script
    d = parser.get_script_description()
    script_group, created = ScriptGroup.objects.get_or_create(group_name=group)
    version_string = d.get('version')
    if version_string is None:
        version_string = '1'
    try:
        parse_version(version_string)
    except:
        sys.stderr.write('Error parsing version, defaulting to 1. Error message:\n {}'.format(traceback.format_exc()))
        version_string = '1'
    if script_version is None:
        # we are being loaded from the management command, create/update our script/version
        script_kwargs = {'script_group': script_group, 'script_name': script_name or d['name']}
        version_kwargs = {'script_version': version_string, 'script_path': local_file, 'default_version': True}
        # does this script already exist in the database?
        script_created = Script.objects.filter(**script_kwargs).count() == 0
        if script_created:
            # we are creating it, add the description if we can
            script_kwargs.update({'script_description': d['description']})
            wooey_script = Script(**script_kwargs)
            wooey_script._script_cl_creation = True
            wooey_script.save()
            version_kwargs.update({'script_iteration': 1})
        else:
            # we're updating it
            wooey_script = Script.objects.get(**script_kwargs)
            if not wooey_script.script_description and d['description']:
                wooey_script.script_description = d['description']
                wooey_script.save()
            # check if we have the version in our script version
            current_versions = ScriptVersion.objects.filter(script=wooey_script, script_version=version_string)
            if current_versions.count() == 0:
                next_iteration = 1
                # disable older versions
                ScriptVersion.objects.filter(script=wooey_script, script_version=version_string).update(default_version=False)
            else:
                # get the largest iteration and add 1 to it
                next_iteration = sorted([i.script_iteration for i in current_versions])[-1]+1
            version_kwargs.update({'script_iteration': next_iteration})
        version_kwargs.update({'script': wooey_script})
        script_version = ScriptVersion(**version_kwargs)
        script_version._script_cl_creation = True
        script_version.save()
    else:
        # we are being created/updated from the admin
        wooey_script = script_version.script
        if not wooey_script.script_description:
            wooey_script.script_description = d['description']
        if not wooey_script.script_name:
            wooey_script.script_name = script_name or d['name']
        past_versions = ScriptVersion.objects.filter(script=wooey_script, script_version=version_string).exclude(pk=script_version.pk)
        script_version.script_iteration = past_versions.count()+1
        past_versions.update(default_version=False)
        script_version.default_version = True
        wooey_script.save()
        script_version.save()

    # make our parameters
    parameter_index = 0
    for param_group_info in d['inputs']:
        param_group_name = param_group_info.get('group')
        param_group, created = ScriptParameterGroup.objects.get_or_create(group_name=param_group_name, script_version=script_version)
        for param in param_group_info.get('nodes'):
            # TODO: fix 'file' to be global in argparse
            is_out = True if (param.get('upload', None) == False and param.get('type') == 'file') else not param.get('upload', False)
            script_param_kwargs = {
                'short_param': param['param'],
                'script_param': param['name'],
                'is_output': is_out,
                'required': param.get('required', False),
                'form_field': param['model'],
                'default': param.get('value'),
                'input_type': param.get('type'),
                'choices': json.dumps(param.get('choices')),
                'choice_limit': json.dumps(param.get('choice_limit', 1)),
                'param_help': param.get('help'),
                'is_checked': param.get('checked', False),
                # parameter_group': param_group,
                'collapse_arguments': 'collapse_arguments' in param.get('param_action', set()),
            }
            parameter_index += 1
            script_params = ScriptParameter.objects.filter(**script_param_kwargs).filter(script_version__script=wooey_script, parameter_group__group_name=param_group_name)
            if not script_params:
                script_param_kwargs['parameter_group'] = param_group
                script_param_kwargs['param_order'] = parameter_index

                script_param, created = ScriptParameter.objects.get_or_create(**script_param_kwargs)
                script_param.script_version.add(script_version)
            else:
                # If we are here, the script parameter exists and has not changed since the last update. We can simply
                # point the new script at the old script parameter. This lets us clone old scriptversions and have their
                # parameters still auto populate.
                script_param = script_params[0]
                script_param.param_order = parameter_index
                script_param.script_version.add(script_version)
                script_param.save()

    return {'valid': True, 'errors': None, 'script': script_version}


def valid_user(obj, user):
    ret = {'valid': False, 'error': '', 'display': ''}
    from ..models import Script
    groups = obj.user_groups.all()

    if wooey_settings.WOOEY_ALLOW_ANONYMOUS or user.is_authenticated():
        if isinstance(obj, Script):
            from itertools import chain
            groups = list(chain(groups, obj.script_group.user_groups.all()))
        if not user.is_authenticated() and wooey_settings.WOOEY_ALLOW_ANONYMOUS and len(groups) == 0:
            ret['valid'] = True
        elif groups:
            ret['error'] = _('You are not permitted to use this script')
        if not groups and obj.is_active:
            ret['valid'] = True
        if obj.is_active == True:
            if set(list(user.groups.all())) & set(list(groups)):
                ret['valid'] = True
    ret['display'] = 'disabled' if wooey_settings.WOOEY_SHOW_LOCKED_SCRIPTS else 'hide'
    return ret


def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_upload_path(filepath, checksum=None):
    filename = os.path.split(filepath)[1]
    if checksum is None:
        checksum = get_checksum(filepath)
    return os.path.join(wooey_settings.WOOEY_FILE_DIR, checksum[:2], checksum[-2:], checksum, filename)


def get_file_info(filepath):
    # returns info about the file
    filetype, preview = False, None
    tests = [('tabular', test_delimited), ('fasta', test_fastx), ('image', test_image)]
    while filetype == False and tests:
        ptype, pmethod = tests.pop()
        filetype, preview = pmethod(filepath)
        filetype = ptype if filetype else filetype
    preview = None if filetype == False else preview
    filetype = None if filetype == False else filetype
    try:
        json_preview = json.dumps(preview)
    except:
        sys.stderr.write('Error encountered in file preview:\n {}\n'.format(traceback.format_exc()))
        json_preview = json.dumps(None)
    return {'type': filetype, 'preview': json_preview}


def test_image(filepath):
    import imghdr
    return imghdr.what(filepath) != None, None


def test_delimited(filepath):
    import csv
    if six.PY3:
        handle = open(filepath, 'r', newline='')
    else:
        handle = open(filepath, 'rb')
    with handle as csv_file:
        try:
            dialect = csv.Sniffer().sniff(csv_file.read(1024*16), delimiters=',\t')
        except Exception as e:
            return False, None
        csv_file.seek(0)
        reader = csv.reader(csv_file, dialect)
        rows = []
        try:
            for index, entry in enumerate(reader):
                rows.append(entry)

        except Exception as e:
            return False, None

        # If > 10 rows, generate preview by slicing top and bottom 5
        # ? this might not be a great idea for massive files
        if len(rows) > 10:
            rows = rows[:5] + [None] + rows[-5:]
        # FIXME: This should be more intelligent:
        # for small files (<1000 rows?) we should take top and bottom preview 10
        # for large files we should give up and present top 10 (11)
        # same rules should apply to columns: this will require us to discard them as they're read

    return True, rows


def test_fastx(filepath):
    # if we can be delimited by + or > we're maybe a fasta/q
    with open(filepath, encoding='latin-1') as fastx_file:
        sequences = OrderedDict()
        seq = []
        header = ''
        found_caret = False
        for row_index, row in enumerate(fastx_file, 1):
            if row_index > 30:
                break
            if not row.strip():
                continue
            if found_caret == False and row[0] != '>':
                if row[0] == ';':
                    continue
                break
            elif found_caret == False and row[0] == '>':
                found_caret = True
            if row and row[0] == '>':
                if seq:
                    sequences[header] = ''.join(seq)
                    seq = []
                header = row
            elif row:
                # we bundle the fastq stuff in here since it's just a visual
                seq.append(row)
        if seq and header:
            sequences[header] = ''.join(seq)
        if sequences:
            rows = []
            [rows.extend([i, v]) for i, v in six.iteritems(sequences)]
            return True, rows
    return False, None


def create_job_fileinfo(job):
    parameters = job.get_parameters()
    from ..models import WooeyFile, UserFile
    # first, create a reference to things the script explicitly created that is a parameter
    files = []
    local_storage = get_storage(local=True)
    for field in parameters:
        try:
            if field.parameter.form_field == 'FileField':
                value = field.value
                if value is None:
                    continue
                if isinstance(value, six.string_types):
                    # check if this was ever created and make a fileobject if so
                    if local_storage.exists(value):
                        if not get_storage(local=False).exists(value):
                            get_storage(local=False).save(value, File(local_storage.open(value)))
                        value = field.value
                    else:
                        field.force_value(None)
                        try:
                            with transaction.atomic():
                                field.save()
                        except:
                            sys.stderr.write('{}\n'.format(traceback.format_exc()))
                        continue
                d = {'parameter': field, 'file': value}
                if field.parameter.is_output:
                    full_path = os.path.join(job.save_path, os.path.split(local_storage.path(value))[1])
                    checksum = get_checksum(value, extra=[job.pk, full_path, 'output'])
                    d['checksum'] = checksum
                files.append(d)
        except ValueError:
            continue

    known_files = {i['file'].name for i in files}
    # add the user_output files, these are things which may be missed by the model fields because the script
    # generated them without an explicit arguments reference in the script
    file_groups = {'archives': []}
    absbase = os.path.join(settings.MEDIA_ROOT, job.save_path)
    for root, dirs, dir_files in os.walk(absbase):
        for filename in dir_files:
            new_name = os.path.join(job.save_path, filename)
            if any([i.endswith(new_name) for i in known_files]):
                continue
            try:
                filepath = os.path.join(root, filename)
                if os.path.isdir(filepath):
                    continue
                full_path = os.path.join(job.save_path, filename)
                # this is to make the job output have a unique checksum. If this file is then re-uploaded, it will create
                # a new file to reference in the uploads directory and not link back to the job output.
                checksum = get_checksum(filepath, extra=[job.pk, full_path, 'output'])
                try:
                    storage_file = get_storage_object(full_path)
                except:
                    sys.stderr.write('Error in accessing stored file {}:\n{}'.format(full_path, traceback.format_exc()))
                    continue
                d = {'name': filename, 'file': storage_file, 'size_bytes': storage_file.size, 'checksum': checksum}
                if filename.endswith('.tar.gz') or filename.endswith('.zip'):
                    file_groups['archives'].append(d)
                else:
                    files.append(d)
            except IOError:
                sys.stderr.write('{}'.format(traceback.format_exc()))
                continue

    # establish grouping by inferring common things
    file_groups['all'] = files
    file_groups['image'] = []
    file_groups['tabular'] = []
    file_groups['fasta'] = []

    for filemodel in files:
        fileinfo = get_file_info(filemodel['file'].path)
        filetype = fileinfo.get('type')
        if filetype is not None:
            file_groups[filetype].append(dict(filemodel, **{'preview': fileinfo.get('preview')}))
        else:
            filemodel['preview'] = json.dumps(None)

    # Create our WooeyFile models

    # mark things that are in groups so we don't add this to the 'all' category too to reduce redundancy
    grouped = set([i['file'].path for file_type, groups in six.iteritems(file_groups) for i in groups if file_type != 'all'])
    for file_type, group_files in six.iteritems(file_groups):
        for group_file in group_files:
            if file_type == 'all' and group_file['file'].path in grouped:
                continue
            try:
                preview = group_file.get('preview')
                size_bytes = group_file.get('size_bytes')

                filepath = group_file['file'].path
                save_path = job.get_relative_path(filepath)
                parameter = group_file.get('parameter')

                # get the checksum of the file to see if we need to save it
                checksum = group_file.get('checksum', get_checksum(filepath))
                try:
                    wooey_file = WooeyFile.objects.get(checksum=checksum)
                    file_created = False
                except ObjectDoesNotExist:
                    wooey_file = WooeyFile(
                        checksum=checksum,
                        filetype=file_type,
                        filepreview=preview,
                        size_bytes=size_bytes,
                        filepath=save_path
                    )
                    file_created = True
                userfile_kwargs = {
                    'job': job,
                    'parameter': parameter,
                    'system_file': wooey_file,
                    'filename': os.path.split(filepath)[1]
                }
                try:
                    with transaction.atomic():
                        if file_created:
                            wooey_file.save()
                        job.save()
                        UserFile.objects.get_or_create(**userfile_kwargs)
                except:
                    sys.stderr.write('Error in saving DJFile: {}\n'.format(traceback.format_exc()))
            except:
                sys.stderr.write('Error in saving DJFile: {}\n'.format(traceback.format_exc()))
                continue


def get_checksum(path, extra=None):
    import hashlib
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    if extra:
        if isinstance(extra, (list, tuple)):
            for i in extra:
                hasher.update(six.u(str(i)).encode('utf-8'))
        elif isinstance(extra, six.string_types):
            hasher.update(extra)
    if isinstance(path, six.string_types):
        with open(path, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
    else:
        start = path.tell()
        path.seek(0)
        buf = path.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = path.read(BLOCKSIZE)
        path.seek(start)
    return hasher.hexdigest()


def get_grouped_file_previews(files):
    groups = {'all': []}
    for file_info in files:
        system_file = file_info.system_file

        filedict = {'id': system_file.id,
                    'object': system_file,
                    'name': file_info.filename,
                    'preview': json.loads(system_file.filepreview) if system_file.filepreview else None,
                    'url': get_storage(local=False).url(system_file.filepath.name),
                    'slug': file_info.parameter.parameter.script_param if file_info.parameter else None,
                    'basename': os.path.basename(system_file.filepath.name),
                    'filetype': system_file.filetype,
                    'size_bytes': system_file.size_bytes,
                    }
        try:
            groups[system_file.filetype].append(filedict)
        except KeyError:
            groups[system_file.filetype] = [filedict]
        if system_file.filetype != 'all':
            groups['all'].append(filedict)
    return groups


def get_file_previews(job):
    from ..models import UserFile
    files = UserFile.objects.filter(job=job)
    return get_grouped_file_previews(files)


def get_file_previews_by_ids(ids):
    from ..models import UserFile
    files = UserFile.objects.filter(pk__in=ids)
    return get_grouped_file_previews(files)


def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    """
    Split the query string into individual keywords, discarding spaces
    and grouping quoted words together.

    >>> normalize_query('  some random  words "with   quotes  " and   spaces')
    ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    """

    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


def get_query(query_string, search_fields):
    """
    Returns a query as a combination of Q objects that query the specified
    search fields.
    """

    query = None  # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None  # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query

    if query is None:
        query = Q()

    return query
