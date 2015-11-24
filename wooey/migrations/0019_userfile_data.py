# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from django.apps import apps
from django.contrib.contenttypes.management import update_contenttypes

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
    for obj in WooeyFile.objects.all():
        user_file = UserFile(filename=os.path.split(obj.filepath.name)[1], job=obj.job,
                             parameter=obj.parameter, system_file=obj)
        user_file.save()
        Favorite.objects.filter(content_type=ctype, object_id=obj.id).update(content_object=obj, content_type=new_ctype)


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0018_userfile'),
    ]

    operations = [
        migrations.RunPython(gen_userfiles),
    ]
