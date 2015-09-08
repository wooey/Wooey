from __future__ import absolute_import
from django.contrib.admin import ModelAdmin, site, TabularInline
from django.forms import ModelForm, ValidationError
from django.utils.translation import ugettext_lazy as _

from .models import Script, ScriptVersion, ScriptGroup, ScriptParameter, WooeyJob, ScriptParameterGroup, WooeyFile


class ScriptVersionForm(ModelForm):
    class Meta:
        model = ScriptVersion
        fields = '__all__'

    def clean(self):
        cleaned = self.cleaned_data
        # make sure we only have 1 default
        current_defaults = ScriptVersion.objects.filter(script=cleaned['script'], default_version=True)
        current_defaults.update(default_version=False)


class JobAdmin(ModelAdmin):
    list_display = ('user', 'job_name', 'script_version', 'status', 'created_date')


class ScriptVersionInline(TabularInline):
    model = ScriptVersion
    extra = 0
    form = ScriptVersionForm


class ScriptAdmin(ModelAdmin):
    list_display = ('script_name', 'script_group', 'is_active')
    inlines = [
        ScriptVersionInline
    ]


class ParameterAdmin(ModelAdmin):
    list_display = ('script_version', 'parameter_group', 'short_param')


class GroupAdmin(ModelAdmin):
    list_display = ('group_name', 'is_active')


class ParameterGroupAdmin(ModelAdmin):
    list_display = ('script_version', 'group_name')


class FileAdmin(ModelAdmin):
    pass

site.register(WooeyJob, JobAdmin)
site.register(WooeyFile, FileAdmin)
site.register(Script, ScriptAdmin)
site.register(ScriptParameter, ParameterAdmin)
site.register(ScriptGroup, GroupAdmin)
site.register(ScriptParameterGroup, ParameterGroupAdmin)
