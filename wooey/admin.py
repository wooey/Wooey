from __future__ import absolute_import
from django.contrib.admin import ModelAdmin, site, TabularInline

from .models import Script, ScriptVersion, ScriptGroup, ScriptParameter, WooeyJob, ScriptParameterGroup, WooeyFile

class JobAdmin(ModelAdmin):
    list_display = ('user', 'job_name', 'script_version', 'status', 'created_date')

class ScriptVersionInline(TabularInline):
    model = ScriptVersion

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
