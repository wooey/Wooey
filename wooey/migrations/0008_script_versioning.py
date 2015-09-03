# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wooey.models.mixins

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
                              'script_path': script.script_path, 'script': last_script,}
            if v[1] == last_script:
                version_kwargs.update({'default_version': True})
            script_version = ScriptVersion(**version_kwargs)
            script_version.save()

def update_script_params(apps, schema_editor):
    Script = apps.get_model("wooey", "Script")
    ScriptVersion = apps.get_model("wooey", "ScriptVersion")
    ScriptParameter = apps.get_model("wooey", "ScriptParameter")
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
                              'script_path': script.script_path, 'script': last_script,}
            if v[1] == last_script:
                version_kwargs.update({'default_version': True})
            script_version = ScriptVersion.objects.get(**version_kwargs)
            for j in ScriptParameter.objects.filter(script=script):
                j.script_version = script_version
                j.save()

def update_script_params_groups(apps, schema_editor):
    Script = apps.get_model("wooey", "Script")
    ScriptVersion = apps.get_model("wooey", "ScriptVersion")
    ScriptParameterGroup = apps.get_model("wooey", "ScriptParameterGroup")
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
                              'script_path': script.script_path, 'script': last_script,}
            if v[1] == last_script:
                version_kwargs.update({'default_version': True})
            script_version = ScriptVersion.objects.get(**version_kwargs)
            for j in ScriptParameterGroup.objects.filter(script=script):
                j.script_version = script_version
                j.save()


class Migration(migrations.Migration):

    dependencies = [
        ('wooey', '0007_script_documentation'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScriptVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('script_version', models.CharField(default='1', help_text='The script version.', max_length=50, blank=True)),
                ('script_iteration', models.PositiveSmallIntegerField(default=1)),
                ('script_path', models.FileField(upload_to=b'')),
                ('default_version', models.BooleanField(default=False)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('script', models.ForeignKey(related_name='script_version_new', to='wooey.Script')),
            ],
            bases=(wooey.models.mixins.ModelDiffMixin, wooey.models.mixins.WooeyPy2Mixin, models.Model),
        ),
        migrations.AddField(
            model_name='scriptparameter',
            name='script_version',
            field=models.ForeignKey(default=1, to='wooey.ScriptVersion'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scriptparametergroup',
            name='script_version',
            field=models.ForeignKey(default=1, to='wooey.ScriptVersion'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='wooeyjob',
            name='script_version',
            field=models.ForeignKey(default=1, to='wooey.ScriptVersion'),
            preserve_default=False,
        ),
        migrations.RunPython(make_script_versions),
        migrations.RunPython(update_script_params),
        migrations.RunPython(update_script_params_groups),
    ]
