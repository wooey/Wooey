from django.contrib import admin

from .models import Script, ScriptGroup, ScriptParameter, DjanguiJob, ScriptParameterGroup

class JobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_name', 'script', 'status', 'created_date')

class ScriptAdmin(admin.ModelAdmin):
    list_display = ('script_name', 'script_group', 'is_active', 'script_version')

class ParameterAdmin(admin.ModelAdmin):
    list_display = ('script', 'parameter_group', 'short_param')

class GroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'is_active')

class ParameterGroupAdmin(admin.ModelAdmin):
    list_display = ('script', 'group_name')

admin.site.register(DjanguiJob, JobAdmin)
admin.site.register(Script, ScriptAdmin)
admin.site.register(ScriptParameter, ParameterAdmin)
admin.site.register(ScriptGroup, GroupAdmin)
admin.site.register(ScriptParameterGroup, ParameterGroupAdmin)