# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def make_script_versions(apps, schema_editor):
    Script = apps.get_model("wooey", "Script")
    ScriptVersion = apps.get_model("wooey", "ScriptVersion")
    ScriptParameter = apps.get_model("wooey", "ScriptParameter")
    ScriptParameterGroup = apps.get_model("wooey", "ScriptParameterGroup")
    WooeyJob = apps.get_model("wooey", "WooeyJob")
    # first group all scripts by name
    from itertools import groupby
    from operator import itemgetter
    scripts = sorted([(i.script_name, i) for i in Script.objects.all()], key=itemgetter(0))
    for script_name, scripts in groupby(scripts, key=lambda x: x[0]):
        # create ScriptVersion from the information in scripts
        ordered_scripts = sorted([(int(script.script_version), script) for i, script in scripts], key=itemgetter(0))
        last_script = ordered_scripts[-1][1]
        for i, v in enumerate(ordered_scripts):
            script = v[1]
            version_kwargs = {'script_version': '1', 'script_iteration': script.script_version,
                              'script_path': script.script_path, 'script': last_script, }
            if v[1] == last_script:
                version_kwargs.update({'default_version': True})
            script_version = ScriptVersion(**version_kwargs)
            script_version.save()
            ScriptParameter.objects.filter(script=script).update(script_version=script_version)
            ScriptParameterGroup.objects.filter(script=script).update(script_version=script_version)
            WooeyJob.objects.filter(script=script).update(script_version=script_version)


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0009_script_versioning'),
    ]

    operations = [
        migrations.RunPython(make_script_versions),
    ]
