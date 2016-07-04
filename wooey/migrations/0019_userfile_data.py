# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import apps
from django.contrib.contenttypes.management import update_contenttypes
from django.db import migrations

from wooey.settings import get as get_setting


def update_all_contenttypes(**kwargs):
    # from http://stackoverflow.com/questions/29550102/importerror-cannot-import-name-update-all-contenttypes
    for app_config in apps.get_app_configs():
        update_contenttypes(app_config, **kwargs)

def gen_userfiles(apps, schema_editor):
    WooeyFile = apps.get_model('wooey', 'WooeyFile')
    UserFile = apps.get_model('wooey', 'UserFile')
    Favorite = apps.get_model('wooey', 'Favorite')
    update_all_contenttypes()
    ContentType = apps.get_model("contenttypes", "ContentType")
    ctype = ContentType.objects.get(model='wooeyfile')
    new_ctype = ContentType.objects.get(model='userfile')
    import os
    checksums = {}
    to_delete = []
    for obj in WooeyFile.objects.all():
        # we only do this for uploads
        if obj.parameter is None or obj.parameter.parameter.is_output == True:
            file_to_use = obj
        else:
            checksum = obj.checksum
            file_to_use = checksums.get(checksum, obj)
            if checksum is not None and checksum not in checksums:
                checksums[checksum] = file_to_use
            if file_to_use != obj:
                to_delete.append(obj.pk)
        user_file = UserFile(filename=os.path.split(obj.filepath.name)[1], job=obj.job,
                             parameter=obj.parameter, system_file=file_to_use)
        user_file.save()
        favorites = Favorite.objects.filter(content_type=ctype, object_id=obj.id)
        for favorite in favorites:
            favorite.content_object = user_file
            favorite.content_type = new_ctype
            favorite.save()
    WooeyFile.objects.filter(pk__in=to_delete).delete()

def setup_wooey_files(apps, schema_editor):
    from six.moves import StringIO
    from django.core.files import File
    from wooey.backend.utils import get_storage

    storage = get_storage()

    WooeyFile = apps.get_model('wooey', 'WooeyFile')
    Favorite = apps.get_model('wooey', 'Favorite')
    WooeyJob = apps.get_model('wooey', 'WooeyJob')
    ScriptParameter = apps.get_model('wooey', 'ScriptParameter')
    ScriptParameters = apps.get_model('wooey', 'ScriptParameters')
    ScriptParameterGroup = apps.get_model('wooey', 'ScriptParameterGroup')
    ScriptVersion = apps.get_model('wooey', 'ScriptVersion')
    Script = apps.get_model('wooey', 'Script')
    User = apps.get_model('auth', 'User')
    update_all_contenttypes()
    ContentType = apps.get_model("contenttypes", "ContentType")
    ctype = ContentType.objects.get(model='wooeyfile')

    user = User.objects.create(username='test user')

    script = Script.objects.create(
        script_name='Test'
    )

    script_version = ScriptVersion.objects.create(
        script=script,
        script_path=get_storage().save('fake_script', File(StringIO('nonsense'))),
    )

    script_parameter_group = ScriptParameterGroup.objects.create(
        group_name='blahh',
        script_version=script_version,
    )

    script_parameter = ScriptParameter.objects.create(
        script_version=script_version,
        short_param='blah',
        script_param='--blah',
        form_field='FileField',
        input_type='file',
        parameter_group=script_parameter_group,
        is_output=False,
    )

    job = WooeyJob.objects.create(
        script_version=script_version,
        job_name='job1',
    )

    job2 = WooeyJob.objects.create(
        script_version=script_version,
        job_name='job2',
    )

    # make wooey files
    buffer = StringIO('file1')
    file1 = get_storage().save('file1', File(buffer))
    file2 = get_storage().save('file1', File(buffer))

    script_parameters = ScriptParameters.objects.create(
        parameter=script_parameter,
        job=job,
        _value=file1,
    )

    script_parameters2 = ScriptParameters.objects.create(
        parameter=script_parameter,
        job=job2,
        _value=file2,
    )


    wooey_file1 = WooeyFile.objects.create(
        filepath=file1,
        job=job,
        parameter=script_parameters,
        checksum='abc123',
    )

    wooey_file1_copy = WooeyFile.objects.create(
        filepath=file2,
        job=job2,
        parameter=script_parameters2,
        checksum='abc123',
    )

    # make the second a favorite file
    Favorite.objects.create(
        content_type=ctype,
        object_id=wooey_file1_copy.pk,
        user=user
    )



def confirm_data_migration(apps, schema_editor):
    WooeyFile = apps.get_model('wooey', 'WooeyFile')
    UserFile = apps.get_model('wooey', 'UserFile')
    Favorite = apps.get_model('wooey', 'Favorite')
    WooeyJob = apps.get_model('wooey', 'WooeyJob')
    ContentType = apps.get_model("contenttypes", "ContentType")
    userfile_type = ContentType.objects.get(model='userfile')

    # We should have one wooeyfile and 2 userfiles
    wooeyfiles = list(WooeyFile.objects.all())
    userfiles = list(UserFile.objects.all())
    assert len(wooeyfiles) == 1
    assert len(userfiles) == 2

    # Ensure favorites now point at UserFiles as well
    favorite = Favorite.objects.first()
    assert favorite.content_type_id == userfile_type.id
    assert favorite.object_id in [i.pk for i in userfiles]

    # Ensure both wooey jobs point at their respective userfiles
    for wooeyjob in WooeyJob.objects.all():
        # There is one one file per wooey job
        assert wooeyjob.userfile_set.first().filename is not None

    # Assert the userfiles all point at the same wooeyfile
    wooeyfile = WooeyFile.objects.first()
    for userfile in UserFile.objects.all():
        assert userfile.system_file_id == wooeyfile.id

def cleanup_tests(apps, schema_editor):
    WooeyFile = apps.get_model('wooey', 'WooeyFile')
    Favorite = apps.get_model('wooey', 'Favorite')
    WooeyJob = apps.get_model('wooey', 'WooeyJob')
    ScriptParameter = apps.get_model('wooey', 'ScriptParameter')
    ScriptParameters = apps.get_model('wooey', 'ScriptParameters')
    ScriptParameterGroup = apps.get_model('wooey', 'ScriptParameterGroup')
    ScriptVersion = apps.get_model('wooey', 'ScriptVersion')
    Script = apps.get_model('wooey', 'Script')
    WooeyFile.objects.all().delete()
    Favorite.objects.all().delete()
    WooeyJob.objects.all().delete()
    ScriptParameter.objects.all().delete()
    ScriptParameters.objects.all().delete()
    ScriptParameterGroup.objects.all().delete()
    ScriptVersion.objects.all().delete()
    Script.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0018_userfile'),
    ]

    operations = []

    if get_setting('TESTING', False):
        operations.append(migrations.RunPython(setup_wooey_files))

    operations.append(
        migrations.RunPython(gen_userfiles),
    )

    if get_setting('TESTING', False):
        operations.append(migrations.RunPython(confirm_data_migration))
        operations.append(migrations.RunPython(cleanup_tests))
