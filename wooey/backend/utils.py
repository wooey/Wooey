from __future__ import absolute_import
__author__ = 'chris'
import json
import errno
import os
import re
import sys
import six
import traceback
from operator import itemgetter
from collections import OrderedDict

from django.conf import settings
from django.db import transaction
from django.db.utils import OperationalError
from django.core.files.storage import default_storage
from django.core.files import File
from django.utils.translation import gettext_lazy as _
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
    from ..models import WooeyFile
    # cleanup the old files, we need to be somewhat aggressive here.
    local_storage = get_storage(local=True)
    for dj_file in WooeyFile.objects.filter(job=job):
        if dj_file.parameter is None or dj_file.parameter.parameter.is_output:
            wooey_file = dj_file.filepath.name
            # this will delete the default file -- which if we are using an ephemeral file system will be the
            # remote instance
            dj_file.filepath.delete(False)
            dj_file.delete()
            # check our local storage and remove it if it is there as well
            path = local_storage.path(wooey_file)
            if local_storage.exists(path):
                local_storage.delete(path)

def get_job_commands(job=None):
    script = job.script
    com = [sys.executable] if sys.executable else []
    com.extend([script.get_script_path()])
    parameters = job.get_parameters()
    param_dict = OrderedDict()
    for param in parameters:
        subproc_dict = param.get_subprocess_value()
        if subproc_dict is None:
            continue
        subproc_param = subproc_dict['parameter']
        if subproc_param not in param_dict:
            param_dict[subproc_param] = []
        subproc_value = subproc_dict.get('value', None)
        if subproc_value:
            param_dict[subproc_param].append(subproc_value)
    for param, values in param_dict.items():
        for value in values:
            if param:
                com.append(param)
            com.append(value)
    return com


@transaction.atomic
def create_wooey_job(user=None, script_pk=None, data=None):
    from ..models import Script, WooeyJob, ScriptParameter, ScriptParameters
    script = Script.objects.get(pk=script_pk)
    if data is None:
        data = {}
    job = WooeyJob(user=user, job_name=data.pop('job_name', None), job_description=data.pop('job_description', None),
                     script=script)
    job.save()
    parameters = OrderedDict([(i.slug, i) for i in ScriptParameter.objects.filter(slug__in=data.keys()).order_by('pk')])
    for slug, param in six.iteritems(parameters):
        slug_values = data.get(slug)
        slug_values = slug_values if isinstance(slug_values, list) else [slug_values]
        for slug_value in slug_values:
            new_param = ScriptParameters(job=job, parameter=param)
            new_param.value = slug_value
            new_param.save()
    return job


def get_master_form(model=None, pk=None):
    from ..forms.factory import DJ_FORM_FACTORY
    return DJ_FORM_FACTORY.get_master_form(model=model, pk=pk)


def get_form_groups(model=None, pk=None, initial_dict=None, render_fn=None):
    from ..forms.factory import DJ_FORM_FACTORY
    return DJ_FORM_FACTORY.get_group_forms(model=model, pk=pk, initial_dict=initial_dict, render_fn=render_fn)


def validate_form(form=None, data=None, files=None):
    form.add_wooey_fields()
    form.data = data if data is not None else {}
    form.files = files if files is not None else {}
    form.is_bound = True
    form.full_clean()


def load_scripts():
    from ..models import Script
    # select all the scripts we have, then divide them into groups
    dj_scripts = {}
    try:
        scripts = Script.objects.count()
    except OperationalError:
        # database not initialized yet
        return
    found_scripts = OrderedDict()
    if scripts:
        scripts = Script.objects.all()
        for script in scripts:
            try:
                found_scripts[script.script_name].append((script.script_version, script))
            except KeyError:
                found_scripts[script.script_name] = [(script.script_version, script)]
    final_scripts = []
    for script_name, scripts in found_scripts.items():
        scripts.sort(key=lambda x: x[0], reverse=True)
        final_scripts.append(scripts[0][1])
    settings.WOOEY_SCRIPTS = final_scripts


def get_storage_object(path, local=False):
    storage = get_storage(local=local)
    obj = storage.open(path)
    obj.url = storage.url(path)
    obj.path = storage.path(path)
    return obj

def add_wooey_script(script=None, group=None):
    from ..models import Script, ScriptGroup, ScriptParameter, ScriptParameterGroup
    # if we have a script, it will at this point be saved in the model pointing to our file system, which may be
    # ephemeral. So the path attribute may not be implemented
    if not isinstance(script, six.string_types):
        try:
            script_path = script.script_path.path
        except NotImplementedError:
            script_path = script.script_path.name

    local_storage = get_storage(local=True)
    if isinstance(script, Script):
        script_obj = script

        # we need to move the script to the wooey scripts directory now
        # handle remotely first, because by default scripts will be saved remotely if we are using an
        # ephemeral file system
        old_name = script.script_path.name
        new_name = os.path.normpath(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, old_name) if not old_name.startswith(wooey_settings.WOOEY_SCRIPT_DIR) else old_name)

        current_storage = get_storage(local=not wooey_settings.WOOEY_EPHEMERAL_FILES)
        current_file = current_storage.open(old_name)
        new_path = current_storage.save(new_name, current_file)

        # remove the old file
        current_storage.delete(old_name)

        script._rename_script = True
        script.script_path.name = new_name
        script.save()

        # download the script locally if it doesn't exist
        if not local_storage.exists(new_path):
            new_path = local_storage.save(new_path, current_file)

        script = get_storage_object(new_path, local=True).path
        local_file = local_storage.open(new_path)
    else:
        script_obj = False
        # we got a path, if we are using a remote file system, it will be located remotely by default
        # make sure we have it locally as well
        if wooey_settings.WOOEY_EPHEMERAL_FILES:
            remote_storage = get_storage(local=False)
            remote_file = remote_storage.open(script)
            local_file = local_storage.save(script, remote_file)
        else:
            local_file = local_storage.open(script)

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
    if script_obj is False:
        script_kwargs = {'script_group': script_group, 'script_description': d['description'],
                         'script_path': script, 'script_name': d['name']}
        scripts = Script.objects.filter(**script_kwargs).order_by('-script_version')
        created = len(scripts) == 0
        if created:
            wooey_script = Script(**script_kwargs)
            wooey_script._script_cl_creation = True
            wooey_script.save()
    else:
        created = False
        if not script_obj.script_description:
            script_obj.script_description = d['description']
        if not script_obj.script_name:
            script_obj.script_name = d['name']
        script_obj.save()
    if not created:
        if script_obj is False:
            wooey_script.script_version += 1
            wooey_script.save()
    if script_obj:
        wooey_script = script_obj
    # make our parameters
    for param_group_info in d['inputs']:
        param_group, created = ScriptParameterGroup.objects.get_or_create(group_name=param_group_info.get('group'), script=wooey_script)
        for param in param_group_info.get('nodes'):
            # TODO: fix 'file' to be global in argparse
            is_out = True if param.get('upload', None) is False and param.get('type') == 'file' else not param.get('upload', False)
            script_param, created = ScriptParameter.objects.get_or_create(script=wooey_script, short_param=param['param'], script_param=param['name'],
                                                                          is_output=is_out, required=param.get('required', False),
                                                                          form_field=param['model'], default=param.get('default'), input_type=param.get('type'),
                                                                          choices=json.dumps(param.get('choices')), choice_limit=json.dumps(param.get('choice_limit', 1)),
                                                                          param_help=param.get('help'), is_checked=param.get('checked', False),
                                                                          parameter_group=param_group)
    return {'valid': True, 'errors': None, 'script': wooey_script}

def valid_user(obj, user):
    groups = obj.user_groups.all()
    from ..models import Script
    ret = {'valid': False, 'error': '', 'display': ''}
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
        if obj.is_active is True:
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


def get_file_info(filepath):
    # returns info about the file
    filetype, preview = False, None
    tests = [('tabular', test_delimited), ('fasta', test_fastx)]
    while filetype is False and tests:
        ptype, pmethod = tests.pop()
        filetype, preview = pmethod(filepath)
        filetype = ptype if filetype else filetype
    preview = None if filetype is False else preview
    filetype = None if filetype is False else filetype
    try:
        json_preview = json.dumps(preview)
    except:
        sys.stderr.write('Error encountered in file preview:\n {}\n'.format(traceback.format_exc()))
        json_preview = json.dumps(None)
    return {'type': filetype, 'preview': json_preview}


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
        for row_index, row in enumerate(fastx_file, 1):
            if row_index > 30:
                break
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
            [rows.extend([i, v]) for i,v in six.iteritems(sequences)]
            return True, rows
    return False, None


def create_job_fileinfo(job):
    parameters = job.get_parameters()
    from ..models import WooeyFile
    # first, create a reference to things the script explicitly created that is a parameter
    files = []
    for field in parameters:
        try:
            if field.parameter.form_field == 'FileField':
                value = field.value
                if value is None:
                    continue
                local_storage = get_storage(local=True)
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
                files.append(d)
        except ValueError:
            continue

    known_files = {i['file'].name for i in files}
    # add the user_output files, these are things which may be missed by the model fields because the script
    # generated them without an explicit arguments reference in the script
    file_groups = {'archives': []}
    absbase = os.path.join(settings.MEDIA_ROOT, job.save_path)
    for filename in os.listdir(absbase):
        new_name = os.path.join(job.save_path, filename)
        if any([i.endswith(new_name) for i in known_files]):
            continue
        try:
            filepath = os.path.join(absbase, filename)
            if os.path.isdir(filepath):
                continue
            full_path = os.path.join(job.save_path, filename)
            try:
                storage_file = get_storage_object(full_path)
            except:
                sys.stderr.write('Error in accessing stored file:\n{}'.format(traceback.format_exc()))
                continue
            d = {'name': filename, 'file': storage_file, 'size_bytes': storage_file.size}
            if filename.endswith('.tar.gz') or filename.endswith('.zip'):
                file_groups['archives'].append(d)
            else:
                files.append(d)
        except IOError:
            sys.stderr.write('{}'.format(traceback.format_exc()))
            continue

    # establish grouping by inferring common things
    file_groups['all'] = files
    import imghdr
    file_groups['image'] = []
    for filemodel in files:
        if imghdr.what(filemodel['file'].path):
            file_groups['image'].append(filemodel)
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

                dj_file = WooeyFile(job=job, filetype=file_type, filepreview=preview, size_bytes=size_bytes,
                                    parameter=group_file.get('parameter'))
                filepath = group_file['file'].path
                save_path = job.get_relative_path(filepath)
                dj_file.filepath.name = save_path
                try:
                    with transaction.atomic():
                        dj_file.save()
                except:
                    sys.stderr.write('Error in saving DJFile: {}\n'.format(traceback.format_exc()))
            except:
                sys.stderr.write('Error in saving DJFile: {}\n'.format(traceback.format_exc()))
                continue


def get_grouped_file_previews(files):
    groups = {'all': []}
    for file_info in files:

        filedict = {'id': file_info.id,
                    'object': file_info,
                    'name': file_info.filepath.name,
                    'preview': json.loads(file_info.filepreview) if file_info.filepreview else None,
                    'url': get_storage(local=False).url(file_info.filepath.name),
                    'slug': file_info.parameter.parameter.script_param if file_info.parameter else None,
                    'basename': os.path.basename(file_info.filepath.name),
                    'filetype': file_info.filetype,
                    'size_bytes': file_info.size_bytes,
                    }
        try:
            groups[file_info.filetype].append(filedict)
        except KeyError:
            groups[file_info.filetype] = [filedict]
        if file_info.filetype != 'all':
            groups['all'].append(filedict)
    return groups


def get_file_previews(job):
    from ..models import WooeyFile
    files = WooeyFile.objects.filter(job=job)
    return get_grouped_file_previews(files)


def get_file_previews_by_ids(ids):
    from ..models import WooeyFile
    files = WooeyFile.objects.filter(pk__in=ids)
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

    query = None # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
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
