# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def gen_userfiles(apps, schema_editor):
    WooeyFile = apps.get_model('wooey', 'WooeyFile')
    UserFile = apps.get_model('wooey', 'UserFile')
    Favorite = apps.get_model('wooey', 'Favorite')
    ContentType = apps.get_model('django', 'ContentType')
    ctype = ContentType.objects.get(model=WooeyFile)
    new_ctype = ContentType.objects.get(model=UserFile)
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
