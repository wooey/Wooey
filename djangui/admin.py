from __future__ import absolute_import
from django.contrib.admin import ModelAdmin, site

from djangui.models import Script, ScriptGroup, ScriptParameter, DjanguiJob, ScriptParameterGroup

class JobAdmin(ModelAdmin):
    list_display = ('user', 'job_name', 'script', 'status', 'created_date')

class ScriptAdmin(ModelAdmin):
    list_display = ('script_name', 'script_group', 'is_active', 'script_version')

class ParameterAdmin(ModelAdmin):
    list_display = ('script', 'parameter_group', 'short_param')

class GroupAdmin(ModelAdmin):
    list_display = ('group_name', 'is_active')

class ParameterGroupAdmin(ModelAdmin):
    list_display = ('script', 'group_name')

site.register(DjanguiJob, JobAdmin)
site.register(Script, ScriptAdmin)
site.register(ScriptParameter, ParameterAdmin)
site.register(ScriptGroup, GroupAdmin)
site.register(ScriptParameterGroup, ParameterGroupAdmin)