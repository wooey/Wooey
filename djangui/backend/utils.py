from __future__ import absolute_import
__author__ = 'chris'
import json
import errno
import os
import sys
import traceback
from operator import itemgetter
from collections import OrderedDict

from django.conf import settings
from django.db import transaction
from django.db.utils import OperationalError
from django.core.files.storage import default_storage
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from celery.contrib import rdb

from .argparse_specs import ArgParseNodeBuilder

from .. import settings as djangui_settings

def sanitize_name(name):
    return name.replace(' ', '_').replace('-', '_')


def sanitize_string(value):
    return value.replace('"', '\\"')

def get_storage(local=True):
    if djangui_settings.DJANGUI_EPHEMERAL_FILES:
        storage = default_storage.local_storage if local else default_storage
    else:
        storage = default_storage
    return storage

def get_job_commands(job=None):
    script = job.script
    com = ['python', script.get_script_path()]
    from ..models import ScriptParameters
    parameters = ScriptParameters.objects.filter(job=job)
    for param in parameters:
        com.extend(param.get_subprocess_value())
    return com

@transaction.atomic
def create_djangui_job(data):
    from ..models import Script, DjanguiJob, ScriptParameter, ScriptParameters
    script = Script.objects.get(pk=data.get('djangui_type'))
    job = DjanguiJob(user=data.get('user'), job_name=data.get('job_name'), job_description=data.get('job_description'),
                     script=script)
    job.save()
    parameters = {i.slug: i for i in ScriptParameter.objects.filter(slug__in=data.keys())}
    for i, v in data.iteritems():
        param = parameters.get(i)
        if param is not None:
            new_param = ScriptParameters(job=job, parameter=param)
            new_param.value = v
            new_param.save()
    return job


def get_master_form(model=None, pk=None):
    from ..forms.factory import DJ_FORM_FACTORY
    return DJ_FORM_FACTORY.get_master_form(model=model, pk=pk)


def get_form_groups(model=None, pk=None, initial=None):
    from ..forms.factory import DJ_FORM_FACTORY
    return DJ_FORM_FACTORY.get_group_forms(model=model, pk=pk, initial=initial)

def validate_form(form=None, data=None, files=None):
    form.add_djangui_fields()
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
    if scripts:
        scripts = Script.objects.all()
        for script in scripts:
            key = (script.script_group.group_order, script.script_group.pk)
            group = dj_scripts.get(key, {
                # 'url': reverse_lazy('script_group', kwargs={'script_group', script.script_group.slug}),
                'group': script.script_group, 'scripts': []
            })
            dj_scripts[key] = group
            try:
                # make sure we can load the form
                get_master_form(script)
                # the url mapping is script_group/script_name
                group['scripts'].append((script.script_order, script))
            except:
                sys.stdout.write('Traceback while loading {0}:\n {1}\n'.format(script, traceback.format_exc()))
                continue
    for group_pk, group_info in dj_scripts.iteritems():
        # order scripts
        group_info['scripts'].sort(key=itemgetter(0))
        group_info['scripts'] = [i[1] for i in group_info['scripts']]
    # order groups
    ordered_scripts = OrderedDict()
    for key in sorted(dj_scripts.keys(), key=itemgetter(0)):
        ordered_scripts[key[1]] = dj_scripts[key]
    settings.DJANGUI_SCRIPTS = ordered_scripts


def get_storage_object(path, local=False):
    storage = get_storage(local=local)
    obj = storage.open(path)
    obj.url = storage.url(path)
    obj.path = storage.path(path)
    return obj

def add_djangui_script(script=None, group=None):
    from djangui.models import Script, ScriptGroup, ScriptParameter, ScriptParameterGroup
    # if we have a script, it will at this point be saved in the model pointing to our file system, which may be
    # ephemeral. So the path attribute may not be implemented
    if not isinstance(script, basestring):
        try:
            script_path = script.script_path.path
        except NotImplementedError:
            script_path = script.script_path.name

    script_obj, script = (script, get_storage_object(script_path, local=True).path) if isinstance(script, Script) else (False, script)
    if isinstance(group, ScriptGroup):
        group = group.group_name
    if group is None:
        group = 'Djangui Scripts'
    basename, extension = os.path.splitext(script)
    filename = os.path.split(basename)[1]

    parser = ArgParseNodeBuilder(script_name=filename, script_path=script)
    if not parser.valid:
        return (False, parser.error)
    # make our script
    d = parser.get_script_description()
    script_group, created = ScriptGroup.objects.get_or_create(group_name=group)
    if script_obj is False:
        djangui_script, created = Script.objects.get_or_create(script_group=script_group, script_description=d['description'],
                                                               script_path=script, script_name=d['name'])
    else:
        created = False
        if not script_obj.script_description:
            script_obj.script_description = d['description']
        if not script_obj.script_name:
            script_obj.script_name = d['name']
        # probably a much better way to avoid this recursion
        script_obj._add_script = False
        script_obj.save()
    if not created:
        if script_obj is False:
            djangui_script.script_version += 1
            djangui_script.save()
    if script_obj:
        djangui_script = script_obj
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
            script_param, created = ScriptParameter.objects.get_or_create(script=djangui_script, short_param=param['param'], script_param=param['name'],
                                                                          is_output=is_out, required=param.get('required', False),
                                                                          form_field=param['model'], default=param.get('default'), input_type=param.get('type'),
                                                                          choices=json.dumps(param.get('choices')), choice_limit=None,
                                                                          param_help=param.get('help'), is_checked=param.get('checked', False),
                                                                          parameter_group=param_group)
    # update our loaded scripts
    load_scripts()
    return (True, '')

def valid_user(obj, user):
    groups = obj.user_groups.all()
    from ..models import Script
    ret = {'valid': False, 'error': '', 'display': ''}
    if isinstance(obj, Script):
        from itertools import chain
        groups = list(chain(groups, obj.script_group.user_groups.all()))
    if not user.is_authenticated() and djangui_settings.DJANGUI_ALLOW_ANONYMOUS and len(groups) == 0:
        ret['valid'] = True
    elif groups:
        ret['error'] = _('You are not permitted to use this script')
    if not groups and obj.is_active:
        ret['valid'] = True
    if obj.is_active is True:
        if set(list(user.groups.all())) & set(list(groups)):
            ret['valid'] = True
    ret['display'] = 'disabled' if djangui_settings.DJANGUI_SHOW_LOCKED_SCRIPTS else 'hide'
    return ret

def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

@transaction.atomic
def create_job_fileinfo(job):
    parameters = job.get_parameters()
    from ..models import DjanguiFile
    # first, create a reference to things the script explicitly created that is a parameter
    files = []
    for field in parameters:
        try:
            if field.parameter.form_field == 'FileField':
                value = field.value
                if value is None:
                    continue
                if isinstance(value, basestring):
                    # check if this was ever created and make a fileobject if so
                    if get_storage(local=True).exists(value):
                        if not get_storage(local=False).exists(value):
                            get_storage(local=False).save(value, File(get_storage(local=True).open(value)))
                        value = field.value
                    else:
                        field.force_value(None)
                        field.save()
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
            d = {'name': filename, 'file': get_storage_object(os.path.join(job.save_path, filename))}
            if filename.endswith('.tar.gz') or filename.endswith('.zip'):
                file_groups['archives'].append(d)
            else:
                files.append(d)
        except IOError:
            print absbase, filename, new_name
            print traceback.format_exc()
            continue


    # establish grouping by inferring common things
    file_groups['all'] = files
    import imghdr
    file_groups['images'] = []
    for filemodel in files:
        if imghdr.what(filemodel['file'].path):
            file_groups['images'].append(filemodel)
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
        # if we can be delimited by + or > we're maybe a fasta/q
        with open(filepath, 'rb') as fastx_file:
            sequences = OrderedDict()
            seq = ''
            header = ''
            for row_index, row in enumerate(fastx_file, 1):
                if row_index > 30:
                    break
                if row and row[0] == '>':
                    if seq:
                        sequences[header] = seq
                        seq = ''
                    header = row
                elif row:
                    # we bundle the fastq stuff in here since it's just a visual
                    seq += row
                if seq and header:
                    sequences[header] = seq
            if sequences:
                rows = []
                [rows.extend([i, v]) for i,v in sequences.iteritems()]
                return True, rows
        return False, None

    for filemodel in files:
        is_delimited, first_rows = test_delimited(filemodel['file'].path)
        if is_delimited:
            file_groups['tabular'].append(dict(filemodel, **{'preview': first_rows}))
        else:
            is_fasta, first_rows = test_fastx(filemodel['file'].path)
            if is_fasta:
                file_groups['fasta'].append(dict(filemodel, **{'preview': first_rows}))

    # Create our DjanguiFile models

    # mark things that are in groups so we don't add this to the 'all' category too to reduce redundancy
    grouped = set([i['file'].path for file_type, groups in file_groups.iteritems() for i in groups if file_type != 'all'])
    for file_type, group_files in file_groups.iteritems():
        for group_file in group_files:
            if file_type == 'all' and group_file['file'].path in grouped:
                continue
            try:
                try:
                    preview = json.dumps(group_file.get('preview'))
                except:
                    sys.stderr.write('Error encountered in file preview:\n {}\n'.format(traceback.format_exc()))
                    preview = None
                dj_file = DjanguiFile(job=job, filetype=file_type, filepreview=preview,
                                    parameter=group_file.get('parameter'))
                filepath = group_file['file'].path
                # make it relative to the root
                dj_file.filepath.name = filepath[filepath.find(settings.MEDIA_ROOT)+len(settings.MEDIA_ROOT)+1:]
                dj_file.save()
            except:
                sys.stderr.write('Error in saving DJFile: {}\n'.format(traceback.format_exc()))
                continue


def get_file_previews(job):
    from ..models import DjanguiFile
    files = DjanguiFile.objects.filter(job=job)
    groups = {'all': []}
    for file_info in files:
        filedict = {'name': file_info.filepath.name, 'preview': json.loads(file_info.filepreview),
                    'url': get_storage(local=False).url(file_info.filepath.name),
                    'slug': file_info.parameter.parameter.script_param if file_info.parameter else None}
        try:
            groups[file_info.filetype].append(filedict)
        except KeyError:
            groups[file_info.filetype] = [filedict]
        if file_info.filetype != 'all':
            groups['all'].append(filedict)
    return groups